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
    { 2, { .valueFloat = 1.0f} },
    { 1, { .valueInt = 1} }
};

int specialCommands[] = {
    0,
    0,
    0
};


#include <mbed.h>

void serialSendCompleteOne(int events);
void serialSendCompleteTwo(int events);
void serialSendCompleteThree(int events);
void serialEventHandler();

void receiveMessage();
void readIncomingBytesIntoBuffer();
void appendByteToBuffer(uint8_t inByte);
void shiftGivenPositionToBufferStart(int position);
int seekForFullMessage();
void extractMessage(int messageStartPosition);


Serial mrSerial(USBTX, USBRX, BAUD_RATE); // tx, rx
Ticker serialReceiver;

Timer dutyCycleTimer;
Timer debugTimer;
unsigned long timeOfLastSend = 0;
unsigned long timeOfLastCompletedMessage = 0;

#define OUT_START_BYTE (char)7
#define OUT_STOP_BYTE (char)8

#define IN_MESSAGE_SIZE 8
#define IN_BUFFER_SIZE ((IN_MESSAGE_SIZE+2)*2)

#define IN_START_BYTE (char)7
#define IN_STOP_BYTE (char)8

unsigned char startOut = 7;
unsigned char endOut = 8;

int duda;
void microRayInit() {
    messageOutBuffer.statusFlags = 0;
    dutyCycleTimer.start();
    // serialReceiver.attach(&readIncomingBytesIntoBuffer, 0.00001f);
    mrSerial.attach(&serialEventHandler, Serial::RxIrq);
}


event_callback_t serialEventWriteCompleteOne = serialSendCompleteOne;
event_callback_t serialEventWriteCompleteTwo = serialSendCompleteTwo;
event_callback_t serialEventWriteCompleteThree = serialSendCompleteThree;
// event_callback_t serialEventHandlerCallback = serialEventHandler;

void serialEventHandler() {
    // mrSerial.printf("eventNumber:");
}


int debugCounterSend = 0;
void serialSendCompleteOne(int events) {
    mrSerial.write((uint8_t *)&messageOutBuffer, sizeof(messageOutBuffer), serialEventWriteCompleteTwo, SERIAL_EVENT_TX_COMPLETE);
}

void serialSendCompleteTwo(int events) {
    mrSerial.write((uint8_t *)&endOut, 1, serialEventWriteCompleteThree, SERIAL_EVENT_TX_COMPLETE);
}

void serialSendCompleteThree(int events) {
    // timeOfLastCompletedMessage = timeOfLastSend;
    lastMessageSendComplete = true;
}



int serialTransmissionLagCounter = 0;
void sendMessage() {

    // decide wether to send in blocking mode or not
    if(lastMessageSendComplete == false) {
        if (sendMode == RECORD_TRANSMISSION_MODE) {
            while(lastMessageSendComplete == false) {
                // wait
            }
        }
        // flag lastMessageSendComplete will never be set to true, don't know why
        // if ((sendMode == LIVE_MODE) && (MESSAGE_SKIP_MODE == 0)) {
        //     while(lastMessageSendComplete == false) {
        //         // wait
        //     }
        // }
    }


    if(lastMessageSendComplete == true) {
        if (sendMode == LIVE_MODE) {
            prepareOutMessage((unsigned long)dutyCycleTimer.read_high_resolution_us());
        }
        lastMessageSendComplete = false;
        // mrSerial.write((uint8_t *)&startOut, 1, serialEventWriteCompleteOne, SERIAL_EVENT_TX_COMPLETE);
    }
    else {
        messageOutBuffer.statusFlags |= (1 << STATUS_SKIPPED);
        serialTransmissionLagCounter++;
        serialTransmissionLag = (float)serialTransmissionLagCounter;
    }
}

uint8_t rawMessageInBuffer[IN_BUFFER_SIZE];
uint8_t rawMessageInBufferTemp[IN_BUFFER_SIZE];
int bufferPosition = 0;

void receiveMessage() {
    int foundMessageStartPosition = seekForFullMessage();
    if(foundMessageStartPosition > -1) {
        extractMessage(foundMessageStartPosition);
        prepareInMessage();
    }
}


void recordMessage() {
    prepareOutMessage((unsigned long)dutyCycleTimer.read_high_resolution_us());
}

void readIncomingBytesIntoBuffer() {
    int i = 0;
    for (i = 0; i < IN_MESSAGE_SIZE; i++) {
        if (mrSerial.readable()) {
            appendByteToBuffer(mrSerial.getc());
        }
        else {
            break;
        }
    }
}

void appendByteToBuffer(uint8_t inByte) {

    // prevent buffer from overfilling
    if(bufferPosition >= IN_BUFFER_SIZE) {
        // shift whole buffer one to the left to free last position
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
