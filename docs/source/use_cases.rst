Use cases for the cranio software
=================================

Example use cases for the cranio software are listed in this section.


.. _distraction-measurement-label:

Distraction measurement
-----------------------

:Use case: Cranial distraction measurement
:Summary: Planned distraction is performed on all distractors by a surgeon and recorded by the software operator.
:Actors: Surgeon and software operator; patient and patient’s parent(s)
:Preconditions: Patient is at the ward for distraction with the patient’s parents, surgeon and operator and the needed equipment at hand.
:Goal for the primary users: Surgeon is able to perform the intended distractions with minimal fuss and yield high quality data; minimizing the amount of discomfort/pain for the patient
:Basic sequence:
    Step 1.
        The operator prepares the application to log data with a torque screw driver (including zeroing the torque) at ward close to the seat where distraction is intended to be performed (typically mains socket available, stable wireless connection is not likely). The operator enters the patient in the application.
    Step 2.
        The parent holds the child patient on his/her laps and stabilizes the head towards the surgeon. Alternatively, the child can be put on his/her stomach on a bed.
    Step 3.
        The operator enters the distractor identifier, or index, in the application. The distractor index is communicated by the surgeon.
    Step 4.
        The surgeon attaches the screw driver (consisting of the driver tip and torque screwdriver attached to a digital torque gauge and laptop) to e.g. a KLS Martin transcutaneously activated distractor fixated to the left most side of cranium of the child and informs the operator that he is ready to start turning the rod of the distractor.
    Step 5.
        The operator starts recording torque data from the screwdriver by clicking "Start" in the application and communicates to the surgeon that the distraction can be started
    Step 6.
        Surgeon turns the distractor slowly and steadily approximately 1/3 of a full turn and monitors the amount of performed rotation from the holes located in the Jacobs Chuck of the screw driver.
    Step 7.
        Surgeon supports the screw driver with the free hand while repositioning the “rotating hand”. No torque applied in this step.
    Step 8.
        Surgeon repeats steps 6 & 7 until 1 full turn has been performed, releases torque from the screw driver and informs the operator.
    Step 9.
        The operator stops data recording by clicking "Stop" in the application. "Stop" triggers an event detection sequence (see next step).
    Step 10.
        The operator marks the distraction events in the event detection window. Alternatively, if in a hurry to continue to the next distraction, the operator can select to mark the distractions later. Operator clicks "Ok" to continue. "Ok" triggers a note window.
    Step 11.
        The operator writes notes and the number of turns performed in the note window and clicks "Finish". "Finish" ends the event detection and returns the application main window.
    Step 12.
        The steps 3 – 11 are repeated on all 2-4 distractors in the child’s cranium typically 3-4 times during one session. Each distractor is typically rotated one full turn and then moved to the next.
:Exceptions:
    Steps 1 & 3.
        The operator may accidentally start data recording without the distraction not immediately ready to start. In this case the operator stops recording and neglects the recorded data.
    Step 4/5-1.
        The surgeon may start turning the distractor too early or not communicate to the operator. The already performed rotation cannot be reversed. Unrecorded distractions are marked in steps 10 & 11.
    Step 4/5-2.
        The data recording may be started too early and artefacts from attaching the screw driver may be induced in the data. Artefacts are to be noted down in step 11 and handled in data analysis.
    Step 6/7.
        The screw driver may slip off from the distractor rod in which case artefacts from the detachment and re-attachment may be induced in the middle of the data. Artefacts are to be noted down in step 11 and handled in data analysis.
    Step 10.
        The software operator is in a hurry to continue the next distraction and therefore flags the distractions to be annotated later.
        This *TODO flagging* is done as follows:

            1. Insert placeholder event regions for each performed distraction
            2. Leave "Done" checkboxes empty
            3. Click "Ok" to continue to the notes dialog
            4. Write notes and number of turns performed in the notes dialog
            5. Click "Finish" to return to the main window

        Data recording for the next distraction can now be started.
        After all the distractions have been performed, the operator annotates the distractions that were not marked as "Done".
    Step 12.
        The surgeon may need to take a several-minute break between distractions if the patient becomes too distressed.
:Postconditions: The planned distraction is performed on all distractors and correctly annotated data is stored at least locally on the laptop. The data may also be uploaded to a central remote data storage.
