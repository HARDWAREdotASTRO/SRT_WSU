
/* Small Radio Telescope - Motor Control
   Winona State University Research
   Clayton G. Hanson
*/

int A_1 = 10;
int A_2 = 9;
int A_PWM = 11;
int RevLimit = 6;
int ForLimit = 7;
int forward_check;
int reverse_check;
int revLimitReach = 0;
int forLimitReach = 0;
int count = 0;
int count_pin = 2;
int lastState = 0;
int switchState = 0;
int k;
int zeroed = 0;

// Serial communication variables
const byte numChars = 32;
char receivedChars[numChars];

boolean newData = false;

int order = 0;
int direct = 0;
int count_till = 0;
int sped = 0;
int request = 0;

void setup() {

  Serial.begin(9600);

  pinMode(A_1, OUTPUT);
  pinMode(A_2, OUTPUT);
  pinMode(A_PWM, OUTPUT);

  digitalWrite(A_1, LOW);
  digitalWrite(A_2, LOW);
  analogWrite(A_PWM, 0);

  pinMode(count_pin, INPUT_PULLUP);
  pinMode(ForLimit, INPUT_PULLUP);
  pinMode(RevLimit, INPUT_PULLUP);

  lastState = digitalRead(count_pin);
}


void loop() {
  counter();
  SerialInputFromPi();
  translateString(request, order, count_till, sped);
  pickFunction(request);
}

void SerialInputFromPi() {

  static boolean recvInProgress = false;
  static byte ndx = 0;
  static boolean overflow = false;
  char startMarker = '<';
  char endMarker = '>';
  char rc;

  while (Serial.available() > 0 && newData == false) {
    rc = Serial.read();
    if (recvInProgress == true) {
      if (rc != endMarker) {
        if (ndx < numChars - 1) {
          receivedChars[ndx] = rc;
          ndx++;
        }
        else {
          overflow = true;
        }
      }
      else {
        receivedChars[ndx] = '\0';
        recvInProgress = false;
        ndx = 0;
        if (overflow == false) {
          newData = true;
        }
        overflow = false;
      }
    }
    else if (rc == startMarker) {
      recvInProgress = true;
      ndx = 0;
      overflow = false;
    }
  }
}
int translateString(int &request, int &order, int &count_till, int &sped) {

  if (newData == true) {
    int newRequest = -1;
    int newOrder;
    int newCount;
    int newSpeed;

    if (sscanf(receivedChars, "%d", &newRequest) == 1) {
      if (newRequest == 9) {
        request = 9;
      }
      else if (newRequest == 0) {
        if (sscanf(receivedChars, "%d,%d,%d,%d",
                   &newRequest,
                   &newOrder,
                   &newCount,
                   &newSpeed) == 4) {
          request = newRequest;
          order = newOrder;
          count_till = newCount;
          sped = newSpeed;
        }
      }
    }
    newData = false;
  }
  return 0;
}
void Move(int &count, int &forLimitReach, int &revLimitReach, int &zeroed) {
  k = count;

  if (count_till != 9999 &&
      zeroed == 1 &&
      k == count_till) {
    direct = 0;
  }
  if (direct == 0) {
    Stop();
    return;
  }
  else if (direct == 1) {
    forward_check = digitalRead(ForLimit);
    if (forward_check == HIGH) {
      Forward();
    }
    else {
      Stop();
      delay(5);
      count = 2005;
      direct = 0;
      forLimitReach = 1;
      zeroed = 1;
    }
  }
  else if (direct == 2) {
    reverse_check = digitalRead(RevLimit);
    if (reverse_check == HIGH) {
      Reverse();
    }
    else {
      Stop();
      delay(5);
      count = 0;
      direct = 0;
      revLimitReach = 1;
      zeroed = 1;
    }
  }
}
int pickFunction(int &request) {
  if (order == 0) {
    direct = 0;
    Move(count, forLimitReach, revLimitReach, zeroed);
  }
  else if (order == 1) {
    direct = 1;
    Move(count, forLimitReach, revLimitReach, zeroed);
  }
  else if (order == 2) {
    direct = 2;
    Move(count, forLimitReach, revLimitReach, zeroed);
  }
  else if (order == 3) {
    GoHome(direct, forLimitReach, revLimitReach);
  }
  else if (order == 4) {
    ZeroSRT(direct, forLimitReach, revLimitReach);
  }
  if (request == 9) {
    k = counter();
    Serial.print(k);
    Serial.println(" ");
    request = 0;
  }
  return 0;
}
int GoHome(int &direct, int &forLimitReach, int &revLimitReach) {
  count_till = 500;
  if (revLimitReach == 0) {
    direct = 2;
    Move(count, forLimitReach, revLimitReach, zeroed);
    if (revLimitReach == 1) {
      direct = 0;
      count = 0;
      delay(100);
    }
    return 0;
  }
  if (count < count_till) {
    direct = 1;
    Move(count, forLimitReach, revLimitReach, zeroed);
    return 0;
  }
  direct = 0;
  order = 0;
  forLimitReach = 0;
  revLimitReach = 0;
  Stop();
  return 1;
}
int ZeroSRT(int &direct, int &forLimitReach, int &revLimitReach) {
  reverse_check = digitalRead(RevLimit);
  if (reverse_check == HIGH) {
    direct = 2;
    Move(count, forLimitReach, revLimitReach, zeroed);
  }
  else {
    Stop();
    count = 0;
    zeroed = 0;
    count_till = 20;
    direct = 1;
    while (count < count_till) {
      Move(count, forLimitReach, revLimitReach, zeroed);
    }
    Stop();
    direct = 0;
    order = 0;
  }
  return 0;
}
void Forward() {
  digitalWrite(A_1, HIGH);
  digitalWrite(A_2, LOW);
  analogWrite(A_PWM, map(constrain(sped, 0, 100), 0, 100, 0, 255));
}
void Reverse() {
  digitalWrite(A_1, LOW);
  digitalWrite(A_2, HIGH);
  analogWrite(A_PWM, map(constrain(sped, 0, 100), 0, 100, 0, 255));
}
void Stop() {
  digitalWrite(A_1, LOW);
  digitalWrite(A_2, LOW);
  analogWrite(A_PWM, 0);
}
int counter() {
  int switchState = digitalRead(count_pin);
  if (switchState != lastState) {
    delay(10);
    switchState = digitalRead(count_pin);
    if (switchState != lastState) {
      if (switchState == HIGH) {
        if (direct == 1) {
          count++;
        }
        if (direct == 2) {
          count--;
        }
      }
      lastState = switchState;
    }
  }
  return count;
}
