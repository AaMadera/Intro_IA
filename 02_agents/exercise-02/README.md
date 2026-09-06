# PEAS description

PEAS description for each application scenario

## Virtual Voice Assitant

- **Performance:** Number of Words transcripted, delay, time to bring the answer
- **Environment:** _Partially observable_ since it starts to record human voice when there is a trigger (like " Hey, Alexa!" to start recording a task).
_Deterministic_, because it needs to send the transcript text to the server to know how to speak back, so the answer is related to the task it heard, for the same reason it is _sequential_.
_Static_ because it needs next human interaction to get a new response.
_Discrete_ since it could split conversation in tokens or words, even if the first raw input is sound and the actions agent/device can take are determined by software code, these are finite.
- **Actuators:** speak, particular sounds (indicating tasks, like done, start to think, hearing, etc...), in software should have some code to send transcript text to the server and get response for the human
- **Sensors:** microphone for hardware, but inside the software libraries to transcript the audio to text, to make the api call to the server, etc...

## Domestic Vacuum robot

- **Performance:** complete tasks per battery cycle, time for each cleaning task, recharging time
- **Environment:** _Partially observable_ It could only see the mapped area for its tasks.
_Deterministic_ I feel like even if the robot needs to evaluate if past section was not fully clean and return, that is part of a plan created by the software algorithm.
_Sequential_ because of the same workflow for achieving the cleaning task.
_Static_ I feel like once the software and memory state that previous path was clean, the robot will not return to validate if there is new dirty. But it could be _Dynamic_ if we consider other humans or pets changing the cleaned floor.
- **Actuators:** mop, water/soap gauge and pump, electric motors
- **Sensors:** Cameras, Lidar sensor

## Recommendations system for streaming service

- **Performance:** User selected how many recommendations
- **Environment:** _Fully observable_ It could query a DB with all the movies the user watched.
_Stochastic_ I feel the algorithm is not only based on user interactions, but in new movies added to catalog, and that is only know until added, cannot predict what will be added in the future.
_Episodic_ for the same reason, any new movie or user interaction could produce different recommendations
_Dynamic_ I feel like the user and platform interaction are always updating.
_Discrete_ everything is save in a DB, so calculations can be done based on that
- **Actuators:** software functions to calculate what to recommend
- **Sensors:** queries to the db to know the user or platform data
