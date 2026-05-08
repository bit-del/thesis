import time
import logging
import numpy as np
import cv2

# --- 對焦指數計算 (Metrics) ---
def compute_score_fluo(image):
    """ [螢光細調] Morphological Opening + Sobel + Top 0.1% Peaks """
    img_float = image.astype(np.float32)
    kernel_size = 13 
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_size, kernel_size))
    structure_only = cv2.morphologyEx(img_float, cv2.MORPH_OPEN, kernel)
    blurred = cv2.GaussianBlur(structure_only, (5, 5), 0)
    gx = cv2.Sobel(blurred, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(blurred, cv2.CV_32F, 0, 1, ksize=3)
    magnitude = cv2.magnitude(gx, gy)
    flat_mag = magnitude.flatten()
    total_pixels = len(flat_mag)
    if total_pixels == 0: return 0.0
    top_n_count = int(total_pixels * 0.001) 
    if top_n_count < 10: top_n_count = 10
    top_gradients = np.partition(flat_mag, -top_n_count)[-top_n_count:]
    score = np.mean(top_gradients ** 2)
    return score

def compute_score_variance(image):
    """ [通用粗調] Global Variance """
    if len(image.shape) == 3:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    score = np.var(image)
    return score

def compute_score_tenengrad(image):
    """ [明視野舊法] Tenengrad """
    img_float = image.astype(np.float32)
    gx = cv2.Sobel(img_float, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(img_float, cv2.CV_32F, 0, 1, ksize=3)
    gradient_sq = gx**2 + gy**2
    score = np.mean(gradient_sq)
    return score

def compute_score_brenner(image):
    """ [明視野新法] Brenner (解決灰塵假峰與相差雙峰) """
    img_float = image.astype(np.float32)
    diff = (img_float[:, 2:] - img_float[:, :-2]) ** 2
    return np.mean(diff)

def compute_score_spatial_frequency(image):
    """ [大範圍單峰] 空間頻率 (結合垂直與水平梯度) """
    img = image.astype(np.float32)
    rf = np.diff(img, axis=0) # 水平
    cf = np.diff(img, axis=1) # 垂直
    rf_score = np.mean(rf**2)
    cf_score = np.mean(cf**2)
    return np.sqrt(rf_score + cf_score)

# --- 自動對焦核心邏輯 (Triple-Metric Dynamic Search) ---
class FocusAlgorithm:
    STATE_IDLE = 0
    STATE_START_STEP = 1
    STATE_SEARCHING = 2
    STATE_FINISHING = 4
    STATE_RECOVERING_PEAK = 5

    def __init__(self, steps_config, status_updater):
        self.steps_config = steps_config
        self.status_updater = status_updater
        logging.info("Dual-Metric N-Stage FocusAlgorithm (Sharp-Centric) initialized.")
        self.reset()

    def reset(self):
        self.state = self.STATE_IDLE
        self.current_step_index = 0
        self.current_step_config = None
        self.direction = -1
        
        self.sharp_last = 0
        self.sharp_max = 0
        self.wide_last = 0
        self.wide_max = 0
        self.sf_last = 0
        self.sf_max = 0
        
        self.drop_count = 0
        self.drop_count_wide = 0
        self.wrong_way_check_done = False 
        
        # 尋峰專用變數
        self.recovery_steps = 0  
        self.recovery_last_value = 0
        self.recovery_drop_count = 0
        self.recovery_max_value = 0

    def start(self, is_fluo_mode=False):
        self.reset()
        self.is_fluo_mode = is_fluo_mode
        mode_label = "Fluo-Centric" if is_fluo_mode else "Triple-Metric BF"
        self.state = self.STATE_START_STEP
        self.status_updater(f"{mode_label} AF started...")

    def cancel(self):
        self.state = self.STATE_IDLE
        self.status_updater("Auto Focus cancelled.")

    def _load_next_step(self):
        if self.current_step_index >= len(self.steps_config):
            self.state = self.STATE_FINISHING
            return False
            
        self.current_step_config = self.steps_config[self.current_step_index]
        self.current_step_index += 1
        
        self.direction *= -1
        
        self.sharp_last = 0
        self.sharp_max = -1 
        self.wide_last = 0
        self.wide_max = -1
        self.sf_last = 0
        self.sf_max = -1
        self.drop_count = 0
        self.drop_count_wide = 0
        self.wrong_way_check_done = False
        
        self.recovery_steps = 0
        self.recovery_last_value = 0
        self.recovery_drop_count = 0
        self.recovery_max_value = 0
        
        step_size, method, _ = self.current_step_config
        self.status_updater(f"AF: Stage {self.current_step_index} (Step: {step_size})")
        return True



    def step(self, wide_metric, sf_metric, sharp_metric):
        if self.state == self.STATE_IDLE:
            return {"type": "WAIT"}

        if self.state == self.STATE_FINISHING:
            self.state = self.STATE_IDLE
            return {"type": "FINISHED"}

        # --- 狀態 1: 準備開始新階段 ---
        if self.state == self.STATE_START_STEP:
            if not self._load_next_step():
                return {"type": "FINISHED"}
            
            self.wide_last = wide_metric
            self.wide_max = wide_metric
            self.sharp_last = sharp_metric
            self.sharp_max = sharp_metric
            self.sf_last = sf_metric
            self.sf_max = sf_metric
            
            self.state = self.STATE_SEARCHING
            step_size, _, _ = self.current_step_config
            command = f"z{step_size * self.direction}"
            return {"type": "MOVE", "command": command}

        # --- 狀態 2: 搜尋中 ---
        if self.state == self.STATE_SEARCHING:
            step_size, _, check_threshold = self.current_step_config
            is_last_stage = (self.current_step_index >= len(self.steps_config))

            # 更新高點紀錄
            if sharp_metric > self.sharp_max:
                self.sharp_max = sharp_metric
            if wide_metric > self.wide_max:
                self.wide_max = wide_metric
            if sf_metric > self.sf_max:
                self.sf_max = sf_metric

            # 根據目前階段選擇主導指標
            if self.is_fluo_mode:
                # 螢光模式：兩階段切換 (Stage 1&2: Var -> Stage 3+: Sharp)
                if self.current_step_index <= 2:
                    active_metric = wide_metric
                    active_last = self.wide_last
                    active_max = self.wide_max
                else:
                    active_metric = sharp_metric
                    active_last = self.sharp_last
                    active_max = self.sharp_max
            else:
                # 明場模式：三階段切換 (Index 1-2: Var -> Index 3: SF -> Index 4+: Sharp)
                if self.current_step_index <= 2:
                    active_metric = wide_metric
                    active_last = self.wide_last
                    active_max = self.wide_max
                elif self.current_step_index == 3:
                    active_metric = sf_metric
                    active_last = self.sf_last
                    active_max = self.sf_max
                else:
                    active_metric = sharp_metric
                    active_last = self.sharp_last
                    active_max = self.sharp_max

            # 【防呆：盲區防護】若剛起步就下跌，說明走錯方向，立刻反轉
            if self.current_step_index == 1:
                if check_threshold and wide_metric < self.wide_last:
                    self.drop_count_wide += 1
                    if self.drop_count_wide == 1 and not self.wrong_way_check_done:
                        self.wrong_way_check_done = True 
                        self.direction *= -1 
                        step = step_size * self.direction * 1.5 
                        self.status_updater(f"AF [Stage 1]: Blind zone, Var dropped. Reversing...")
                        self.wide_last = wide_metric
                        self.drop_count_wide = 0
                        return {"type": "MOVE", "command": f"z{step}"}
                else:
                    self.drop_count_wide = 0

            # 【核心：根據當前指標找山頂】
            passed_peak = False
            
            # --- 判斷邏輯 1: 顯著下跌 (最高點 80% 閾值) ---
            # 只要分數跌過峰值 0.8 則生效 (保留極低噪音過濾 > 10)
            is_valid_signal = (active_max > 10.0)
            
            if is_valid_signal and (active_metric / active_max) < 0.8:
                passed_peak = True
                self.status_updater(f"AF [Stage {self.current_step_index}]: Sharp drop detected ({active_metric / active_max:.2f} < 0.8). Peak passed.")

            # --- 判斷邏輯 2: 連續下跌數 (Trend backup) ---
            if active_metric < active_last:
                self.drop_count += 1
                max_drops = 3 if step_size <= 5 else 2
                
                if not passed_peak and is_valid_signal and self.drop_count >= max_drops:
                    passed_peak = True
                    self.status_updater(f"AF [Stage {self.current_step_index}]: Consecutive drops ({self.drop_count}). Peak passed.")
            else:
                self.drop_count = 0

            # --- 通過巔峰後的處理 ---
            if passed_peak:
                if is_last_stage:
                    self.status_updater(f"AF: Peak Passed. Reversing ({active_max:.2e})...")
                    self.state = self.STATE_RECOVERING_PEAK
                    self.direction *= -1     
                    self.recovery_steps = 0  
                    self.recovery_last_value = active_metric
                    self.recovery_max_value = active_metric
                    self.recovery_drop_count = 0
                    return {"type": "MOVE", "command": f"z{step_size * self.direction}"}
                else:
                    step = step_size * self.direction * -1 
                    self.status_updater(f"AF: Peak Passed. Stage {self.current_step_index} completed.")
                    self.state = self.STATE_START_STEP
                    return {"type": "MOVE", "command": f"z{step}"}
            else:
                self.drop_count = 0
            
            self.sharp_last = sharp_metric
            self.wide_last = wide_metric
            self.sf_last = sf_metric
            return {"type": "MOVE", "command": f"z{step_size * self.direction}"}
        
        # --- 狀態 5: 往回尋找最高點 (Closed-loop Peak Recovery) ---
        if self.state == self.STATE_RECOVERING_PEAK:
            step_size, _, _ = self.current_step_config
            self.recovery_steps += 1
            
            if sharp_metric >= self.sharp_max * 0.98:
                self.status_updater(f"AF: Peak locked! Final Score: {sharp_metric:.2e}")
                self.state = self.STATE_FINISHING
                return {"type": "FINISHED"} 
                
            if sharp_metric > self.recovery_max_value:
                self.recovery_max_value = sharp_metric
                
            if sharp_metric < self.recovery_last_value:
                self.recovery_drop_count += 1
            else:
                self.recovery_drop_count = 0
                
            self.recovery_last_value = sharp_metric
            
            if self.recovery_drop_count >= 2:
                # 取得當前的主導最高點以進行回溯回傳（此處簡化為使用 sharp_max，通常最後一階段就是 sharp）
                target_value = self.sharp_max
                self.direction *= -1
                self.recovery_drop_count = 0
                self.status_updater(f"AF [Recovering]: Passed local peak! Target {target_value * 0.98:.2e}. Reversing...")
                return {"type": "MOVE", "command": f"z{step_size * self.direction}"}

            if self.recovery_steps > 20: 
                self.status_updater(f"AF: Recovery timeout. Stopping at current position.")
                self.state = self.STATE_FINISHING
                return {"type": "FINISHED"}
                
            return {"type": "MOVE", "command": f"z{step_size * self.direction}"}
            
        return {"type": "WAIT"}