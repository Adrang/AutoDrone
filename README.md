AutoDrone
===========================

This project is licensed under the terms of the MIT license and was originally undertaken to fulfill the requirements for a graduate level independent study towards the completion of the Master's of Computer Science at Rochester Institute of Technology.

- [AutoDrone Proposal](docs/AutoDrone_proposal.pdf)
- [AutoDrone Writeup](docs/AutoDrone_writeup.pdf)

## Roadmap
## Hardware Guide
### In Theory
### In Practice
## Software Guide

### ControlCli
### ControlGui

## Future Work

## Expected operation

Upon initially turning on the Tello drone, the indicator led blink green and then flash red for about 1 second. It will then switch off for another second, and then proceed to blink a series of colors. Eventually, it will continually flash yellow. At this point, the drone should be broadcasting its wifi network and you should be able to connect to it from your computer's network settings. [A video of this sequence is located in the `docs` folder.](docs/indicator_led_sequence.mp4)

When the GUI or CLI utilities are run, they will send 'command' to the drone. This specific string tells the drone to switch to sdk mode, allowing us to use our program to send commands to control the drone. The utilities keep sending this command on a 1 second interval until the receive an 'ok' message, indicating that the drone has successfully received the command. At this point, the utility has established a connection to the drone, and the user is able to interactively send control the Tello drone from the utility's interface.

### Command descriptions

#### 

## License

See the [LICENSE file](LICENSE) for license rights and limitations (MIT).
