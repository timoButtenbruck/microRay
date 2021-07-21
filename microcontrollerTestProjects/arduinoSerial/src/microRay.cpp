#include "microRay.h"

void prepareOutMessage();
void prepareInMessage();
void sendMessage();
void receiveMessage();
void record();
void recordMessage();
void transmitRecordings();

unsigned long lastTime = 0;
volatile bool lastMessageSendComplete = true;

int sendMode = LIVE_MODE;
int recordingCounter = 0;
int recordingSendCounter = 0;


// storage for unrequested channels
float unrequestedChannels[CHANNELS_UNREQUESTED_COUNT];

#if !defined(SUPPRESS_PARAM_CONFIRMATION)
int parameterSendCounter = 0;
#endif

int receivedBytesCount = 0;
int sendBytesCount = 0;

MessageOut messageOutBuffer;
MessageIn messageInBuffer;

MessageOut recordBuffer[RECORD_BUFFER_LENGTH];

void prepareOutMessage(unsigned long loopStartTime)
{
    // map rotating parameters
    // on each cycle, only one of the "controlled parameters" is send to the pc

    messageOutBuffer.loopStartTime = loopStartTime;

    #if !defined(SUPPRESS_PARAM_CONFIRMATION)
    messageOutBuffer.parameterNumber = parameterSendCounter;
    if (parameterSendCounter < 0) {
        messageOutBuffer.parameterValueInt = specialCommands[(parameterSendCounter + 1) * -1];
    }
    else {
        switch (parameters[parameterSendCounter].dataType) {
            case INT_TYPE:
                messageOutBuffer.parameterValueInt = parameters[parameterSendCounter].valueInt;
                break;
            case FLOAT_TYPE:
                messageOutBuffer.parameterValueFloat = parameters[parameterSendCounter].valueFloat;
                break;
            default:
                break;
        }
    }

    // increment the counter for sending the "slow parameters"
    parameterSendCounter += 1;
    if (parameterSendCounter >= PARAMETER_COUNT)
    {
        parameterSendCounter = SPECIAL_COMMANDS_COUNT * -1;
    }
#endif
}

void prepareInMessage() {
    if (messageInBuffer.parameterNumber >= 0) {
        switch (parameters[messageInBuffer.parameterNumber].dataType) {
            case INT_TYPE:
                parameters[messageInBuffer.parameterNumber].valueInt = messageInBuffer.parameterValueInt;
                break;
            case FLOAT_TYPE:
                parameters[messageInBuffer.parameterNumber].valueFloat = messageInBuffer.parameterValueFloat;
                break;
            default:
                break;
        }
    }
    else {
        // toggle recording mode
        if (messageInBuffer.parameterNumber == -3) {
            if (messageInBuffer.parameterValueInt != specialCommands[(messageInBuffer.parameterNumber + 1) * -1]) {
                if (messageInBuffer.parameterValueInt == 1) {
                    sendMode = RECORD_MODE;
                }
                else if (messageInBuffer.parameterValueInt == 0) {
                    sendMode = RECORD_TRANSMISSION_MODE;
                }
            }
        }
        specialCommands[(messageInBuffer.parameterNumber + 1) * -1] = messageInBuffer.parameterValueInt;
    }
}

void microRayCommunicate()
{
    receiveMessage();

#ifndef mrDEBUG
    switch (sendMode) {
        case RECORD_MODE:
            record();
            break;
        case RECORD_TRANSMISSION_MODE:
            transmitRecordings();
            break;
        case LIVE_MODE:
            sendMessage();
            break;
        case WAIT_MODE:
            break;
        default:
            break;
    }
#endif
}

void record() {
    recordMessage();
    recordBuffer[recordingCounter] = messageOutBuffer;
    recordingCounter += 1;
    if (recordingCounter > RECORD_BUFFER_LENGTH) {
        recordingCounter = 0;
    }
}

void transmitRecordings() {
    // blocks until finished
    for (recordingSendCounter = 0; recordingSendCounter < RECORD_BUFFER_LENGTH; recordingSendCounter++) {
        int nextMessageIndex = recordingSendCounter + recordingCounter;
        if (nextMessageIndex > RECORD_BUFFER_LENGTH){
            nextMessageIndex -= RECORD_BUFFER_LENGTH;
        }
        messageOutBuffer = recordBuffer[nextMessageIndex];
        sendMessage();
        receiveMessage();
        // while (lastMessageSendComplete == false) {
            // wait
        // }
    }
    recordingCounter = 0;
    sendMode = WAIT_MODE;
}

Parameter parameters[] = {
    { 2, { .valueFloat = 3.0f} }
};

int specialCommands[] = {
    0,
    0,
    0
};


#include <arduino.h>

void receiveMessage();
void readIncomingBytesIntoBuffer();
void appendByteToBuffer(uint8_t inByte);
void shiftGivenPositionToBufferStart(int position);
int seekForFullMessage();
void extractMessage(int messageStartPosition);


#define OUT_START_BYTE (char)7
#define OUT_STOP_BYTE (char)8

#define IN_MESSAGE_SIZE 8
#define IN_BUFFER_SIZE ((IN_MESSAGE_SIZE+2)*2)

#define IN_START_BYTE (char)7
#define IN_STOP_BYTE (char)8

int serialBufferSize = 0;
void microRayInit() {
    messageOutBuffer.statusFlags = 0;
    Serial.begin(BAUD_RATE);
    serialBufferSize = Serial.availableForWrite();
}


void sendMessage() {
    if (sendMode == LIVE_MODE) {
        prepareOutMessage(micros());
    }

    // check, if there is still data not send from the previous loop
    #ifdef SERIAL_TX_BUFFER_SIZE
        int bytesStillInBuffer = SERIAL_TX_BUFFER_SIZE - Serial.availableForWrite();
        if (bytesStillInBuffer > 1) {
            messageOutBuffer.statusFlags |= (1 << STATUS_SKIPPED);
            serialTransmissionLag = bytesStillInBuffer;
        }
    #endif

    lastMessageSendComplete = false;
    Serial.write(7);
    Serial.write((byte *)&messageOutBuffer, sizeof(messageOutBuffer));
    Serial.write(8);

    // wait for message to complete during recording transfer
    if (sendMode == RECORD_TRANSMISSION_MODE) {
        while (Serial.availableForWrite() < serialBufferSize) {
            // wait
        }
        lastMessageSendComplete = true;
    }
}


void recordMessage() {
    prepareOutMessage(micros());
}




uint8_t rawMessageInBuffer[IN_BUFFER_SIZE];
uint8_t rawMessageInBufferTemp[IN_BUFFER_SIZE];
int16_t bufferPosition = 0;

void receiveMessage() {
    readIncomingBytesIntoBuffer();
    int foundMessageStartPosition = seekForFullMessage();

    if(foundMessageStartPosition > -1) {
        extractMessage(foundMessageStartPosition);
        prepareInMessage();
    }
}

void readIncomingBytesIntoBuffer() {
    while (Serial.available()) {
        appendByteToBuffer(Serial.read());
    }
}

void appendByteToBuffer(uint8_t inByte) {
    // prevent buffer from overfilling
    // shift whole buffer one to the left to free last position
    if(bufferPosition >= IN_BUFFER_SIZE) {
        shiftGivenPositionToBufferStart(1);
    }
    rawMessageInBuffer[bufferPosition] = inByte;
    bufferPosition += 1;
}

void shiftGivenPositionToBufferStart(int position) {
    // copy and shift
    int i;
    for(i = position; i < bufferPosition; i++) {
        rawMessageInBufferTemp[i - position] = rawMessageInBuffer[i];
    }

    // actualize bufferPosition
    bufferPosition = bufferPosition - position;

    // copy back
    for(i = 0; i < bufferPosition; i++) {
        rawMessageInBuffer[i] = rawMessageInBufferTemp[i];
    }
}

int seekForFullMessage() {
    int i;
    for (i = 0; i < bufferPosition - IN_MESSAGE_SIZE; i++) {
        if (rawMessageInBuffer[i] == IN_START_BYTE) {
            int expectedStopBytePosition = i + IN_MESSAGE_SIZE + 1;
            if (rawMessageInBuffer[expectedStopBytePosition] == IN_STOP_BYTE) {
                return i;
            }
        }
    }
    return -1;
}

void extractMessage(int messageStartPosition) {
    memcpy(&messageInBuffer.parameterNumber, &rawMessageInBuffer[messageStartPosition + 1], 4);
    memcpy(&messageInBuffer.parameterValueInt, &rawMessageInBuffer[messageStartPosition + 1 + 4], 4);
    shiftGivenPositionToBufferStart(messageStartPosition + IN_MESSAGE_SIZE + 2);
}
