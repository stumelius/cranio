Use cases for cranio
====================

.. todo:: To be documented

Distraction measurement
-----------------------

:Use case: Cranial distraction measurement
:Summary: .. todo:: To be documented
:Actors: Surgeon and software operator; patient and patient’s parent(s)
:Preconditions: Patient is at the ward for distraction with the patient’s parents, surgeon and operator and the needed equipment at hand.
:Goal for the primary users: Surgeon is able to perform the intended distractions with minimal fuss and yield high quality data; minimizing the amount of discomfort/pain for the patient
:Basic sequence - Step 1: The operator prepares the application to log data with a torque screw driver (including zeroing the torque) at ward close to the seat where distraction is intended to be performed (typically mains socket available, stable wireless connection is not likely). The operator enters the patient in the application.
:Basic sequence - Step 2: The parent holds the child patient on his/her laps and stabilizes the head towards the surgeon. Alternatively, the child can be put on his/her stomach on a bed.
:Basic sequence - Step 3: The operator enters the distractor identifier, or index, in the application. The distractor index is communicated by the surgeon.
:Basic sequence - Step 4: The surgeon attaches the screw driver (consisting of the driver tip and torque screwdriver attached to a digital torque gauge and laptop) to e.g. a KLS Martin transcutaneously activated distractor fixated to the left most side of cranium of the child and informs the operator that he is ready to start turning the rod of the distractor.
:Basic sequence - Step 5: The operator starts recording torque data from the screwdriver by clicking "Start" in the application and communicates to the surgeon that the distraction can be started
:Basic sequence - Step 6: Surgeon turns the distractor slowly and steadily approximately 1/3 of a full turn and monitors the amount of performed rotation from the holes located in the Jacobs Chuck of the screw driver.
:Basic sequence - Step 7: Surgeon supports the screw driver with the free hand while repositioning the “rotating hand”. No torque applied in this step.
:Basic sequence - Step 8: Surgeon repeats steps 6 & 7 until 1 full turn has been performed, releases torque from the screw driver and informs the operator.
:Basic sequence - Step 9: The operator stops data recording by clicking "Stop" in the application. "Stop" triggers an event detection sequence (see next step).
:Basic sequence - Step 10: The operator marks the distraction events in the event detection window. Alternatively, if in a hurry to continue to the next distraction, the operator can select to mark the distractions later. Operator clicks "Ok" to continue. "Ok" triggers a note window.
:Basic sequence - Step 11: The operator writes notes and the number of turns performed in the note window and clicks "Finish". "Finish" ends the event detection and returns the application main window.
:Basic sequence - Step 12: The steps 3 – 11 are repeated on all 2-4 distractors in the child’s cranium typically 3-4 times during one session. Each distractor is typically rotated one full turn and then moved to the next.
:Exceptions: .. todo:: To be documented
:Postconditions: .. todo:: To be documented
