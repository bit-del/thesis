/*
 * 3軸步進馬達控制器 (使用 AccelStepper 函式庫)
 * * - 支援 G-code 般的序列埠指令 (例如：x50, y-100)
 * - 實現了平滑的加減速控制
 * - 可在下方 "使用者設定" 區域輕鬆反轉各軸方向
 * - 【新增】支援長短距離不同速度
 */

#include <AccelStepper.h>

// ----------------------------------------------------
// --------------- ⚙️ 使用者設定 ⚙️ -----------------
// ----------------------------------------------------

// 1. 定義步進馬達驅動器引腳
const int StepX = 2;
const int DirX = 5;
const int StepY = 3;
const int DirY = 6;
const int StepZ = 4;
const int DirZ = 7;

// 2. 設定馬達速度與加速度
//    您可以根據您的馬達和機構調整這些數值
const float maxSpeed = 800.0;      // 【修改】常規 (短距離) 最大速度 (步/秒)
const float highSpeed = 16000.0;   // 【新增】長距離 (超過100步) 用的高速 (步/秒)
const float acceleration = 160000.0; // 加速度 (步/秒^2)

// 3. 設定各軸運動方向
//    如果某個軸的運動方向與您預期的相反，請將 'false' 改為 'true'
const bool invertX = false; // X 軸是否反轉
const bool invertY = true;  // Y 軸是否反轉
const bool invertZ = true; // Z 軸是否反轉

// ----------------------------------------------------
// ----------------- 程式碼開始 -------------------
// ----------------------------------------------------

// 定義驅動器介面類型 (A4988, DRV8825 等標準驅動器)
#define DRIVER_INTERFACE AccelStepper::DRIVER

// 建立 AccelStepper 物件
AccelStepper stepperX(DRIVER_INTERFACE, StepX, DirX);
AccelStepper stepperY(DRIVER_INTERFACE, StepY, DirY);
AccelStepper stepperZ(DRIVER_INTERFACE, StepZ, DirZ);

void setup() {
  Serial.begin(9600);

  // --- 設定 X 軸 ---
  // setPinsInverted(bool dirInvert, bool stepInvert, bool enableInvert)
  stepperX.setPinsInverted(invertX, false, false);
  stepperX.setMaxSpeed(maxSpeed); // 設定預設速度
  stepperX.setAcceleration(acceleration);

  // --- 設定 Y 軸 ---
  stepperY.setPinsInverted(invertY, false, false);
  stepperY.setMaxSpeed(maxSpeed); // 設定預設速度
  stepperY.setAcceleration(acceleration);

  // --- 設定 Z 軸 ---
  stepperZ.setPinsInverted(invertZ, false, false);
  stepperZ.setMaxSpeed(maxSpeed); // 設定預設速度
  stepperZ.setAcceleration(acceleration);

  Serial.println("Arduino Motor Controller Ready (AccelStepper).");
  Serial.println("Waiting for commands like 'x50' or 'z-20'...");
}

void loop() {
  // 檢查序列埠是否有可讀取的資料
  if (Serial.available() > 0) {
    // 讀取整行指令，直到換行符為止
    String input = Serial.readStringUntil('\n');
    input.trim(); // 移除頭尾的空白字符
    if (input.length() > 0) {
      // 解析並執行指令
      parseAndExecute(input);
    }
  }
}

/*
 * 【已移除】
 * 舊的 moveMotor() 函數已被 AccelStepper 的功能取代，
 * 其加減速和脈衝產生由函式庫在後台處理。
 */

// 【修改】整個函數的邏輯以支援動態速度
void parseAndExecute(String input) {
  // 指令格式: [軸][步數], 例如：x50, y-100, z20
  if (input.length() < 2) {
    Serial.println("Error: Invalid command format.");
    return;
  }
  
  char axis = input.charAt(0);
  String valueStr = input.substring(1);
  long steps = valueStr.toInt();

  if (steps == 0) {
    Serial.println("OK"); // 即使 0 步也要回傳 OK
    return;
  }
  
  // 【新增】根據距離判斷要使用的速度
  // abs(steps) 用於取得步數的絕對值，無論正轉反轉
  float targetSpeed;
  if (abs(steps) > 1000) {
    targetSpeed = highSpeed; // 距離 > 1000，使用高速
  } else {
    targetSpeed = maxSpeed;  // 距離 <= 1000，使用常規速度
  }

  // 根據軸選擇目標馬達
  switch (axis) {
    case 'x':
    case 'X':
      // 1. 【新增】為這次移動設定目標速度
      stepperX.setMaxSpeed(targetSpeed);
      // 2. 設定相對移動的步數
      stepperX.move(steps);
      // 3. 執行移動 (這是一個阻塞型函數，會在此處等待直到移動完成)
      stepperX.runToPosition();
      break;
    case 'y':
    case 'Y':
      // 1. 【新增】為這次移動設定目標速度
      stepperY.setMaxSpeed(targetSpeed);
      // 2. 設定相對移動的步數
      stepperY.move(steps);
      // 3. 執行移動
      stepperY.runToPosition();
      break;
    case 'z':
    case 'Z':
      // 1. 【新增】為這次移動設定目標速度
      stepperZ.setMaxSpeed(targetSpeed);
      // 2. 設定相對移動的步數
      stepperZ.move(steps);
      // 3. 執行移動
      stepperZ.runToPosition();
      break;
    default:
      Serial.print("Error: Unknown axis '");
      Serial.print(axis);
      Serial.println("'");
      return; // 如果軸無法識別，則退出
  }

  // 移動完成後，印出確認訊息
  Serial.println("OK");
}