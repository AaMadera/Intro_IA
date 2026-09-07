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

## Autonomous vehicle at city

- **Performance:** kms per W, score of each obstacle identified (like pedestrians, other vehicles, signs), situations and time the person took the control or provided feedback
- **Environment:**
_Partially observable_ The surrounding is in constant change when the vehicle is in motion.
_Stochastic_ as the real world interaction is very different than a fix set of conditions, feel like there could be several functions the car can have to face all the problems in the road, but the variables to consider are so many and chaotic, I don't think the real world scenarios can be considered "Deterministic", at least when a lot of variables are considered.
_Dynamic_ Because every centimeter the vehicle moves there's a drastic change in the variables
_Continuos_ The vars can be discretized for coding and signal processing, but these change and are measured at very high frequencies that we can considered them continuos all the time.
- **Actuators:** Motor, pedals, direction steer, lights, etc...
- **Sensors:** lidar, cameras, proximity sensors, light sensors, etc...

## Trading Agent

- **Performance:** Amount lose or earned, time of response, statistic variables
- **Environment:** _Partially observable_ Because it doesn't require to have all history of for example all the previous stock values, it just require to see trending lines/functions, based on that it will take decision for selling or buying, like, if the prices ir higher or lower than the goal and based on slop of the trending if going up or low the reference
_Stochastic_ Yes because it cannot predict the future values, I mean, trends help to stimate future behaviors but these cannot be 100% true, the variables affecting stock values are a lot.
_Episodic_ It should apply sell/buy actions based on the current stoke values, instead of what happened in the past.
_Dynamic_ Everything is changing while the agent is thinking or processing.
- **Actuators:** sell function, buy function
- **Sensors:** trending reference, current money status, current stock values

## AI assisted Medical diagnostic system

- **Performance:** Time to find the diagnostic, percentage of good findings
- **Environment:** _Fully observable_ Because the entry should be fixed, I mean, the current blood pressure, metrics of each chemical reference is measured and read once, etc.. Like the current status of the patient is a screenshot to analyze.
_Deterministic_ same input should produce same output of the diagnostic, or close to the same, since it is based on current fixed variables values.
_Sequential_ because the collection of certain symptoms or chemical values could lead to some specific diagnostic related to those values.
_Static_ The current diagnostic could not evolve so fast in a person (if we are not talking about real urgencies)
_Discrete_ I feel like we can convert some chemical values to normal, good or bad status to later create score or collection of symptoms that could lead to a collection of possible problems
- **Actuators:** functions to compare values against standards of good or bad symptoms
- **Sensors:** read current chemical values, patient history search

## Drone for infrastructure inspection

- **Performance:** Error of the registered measures, battery consumption per task, time to analyze each aspect related to final results
- **Environment:** _Fully observable_ the structures are usually statics and do not vary that often, like a building.
_Deterministic_ Doing the same inspection should reflect same results, the status of a building structure do not change that much/fast
_episodic_ I feel like measures are independent and should not affect among each other
_static_ the variable values should remain the same under the inspections
_discrete_ I feel like each measure can be specified as a number.
- **Actuators:** Propellers, lights, remote control
- **Sensors:** gps, camera, sensors that will take measures of different things.

## Chess player agent

- **Performance:** count/percentage of wins, number of movements to win/lose, time to think next move, algorithm complexity
- **Environment:** _Fully observable_ dashboard, pieces are totally observable
_Deterministic_ if you apply the same movements could lead to same results
_sequential_ current or past status of the game should result in losing pieces or get close to win
_static_ opponent pieces are not moving until agent make a move
_discrete_ movements and pieces are totally specified
- **Actuators:** function to move a piece, functions to create next move strategy
- **Sensors:** read movement of the opponent, function to read from memory current status of the game
