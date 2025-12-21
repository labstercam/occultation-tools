# Occulation Manager

SharpCap Occulation Manager for Occult Watcher Cloud
SharpCap Occultation Manager for Occult Watcher is a tool for SharpCap that fully automates occultation observations. It downloads personal observations announced in Occult Watcher Cloud. It includes an Event Manager to manage events, Sequence generation to create SharpCap sequences for doing the recordings (either in the tool itself or by using the sequences directly), and configuration management.

The tool serves several purposes:

1. Enables full automation of observations from SharpCap, only requiring the use of OW Cloud to announce stations
2. Provides a much simplified work-flow for SharpCap users - other tools usually require the use of Occult Watcher Desktop or Occult 4 to generate or manage predictions, with a lot of manual work to select and run the observations, even with the OWD SharpCap addins
3. Provides a very easy and flexible way to generate SharpCap sequences to record events, with the ability for the user to edit the sequence template to their needs or edit the generate sequences

How to Install the SharpCap Addin
1. Download the Python code from ??? by right clicking and selecitng 'Save As'
2. Unzip to a file locaiton where you have read/write access. Suggest a new subfolder  \Documents\Sharpcap\occultation-manager
3.Start SharpCap
4. In "File" - "SharpCap Settings" - "Startup Scripts" - find that folder and add the 'main' script

<img width="666" height="155" alt="image" src="https://github.com/user-attachments/assets/42a9d9c9-4273-4a88-8d0a-428cca649afe" />

5. Close SharpCap (the script will be loaded at the next start)

A new button should appear in the SharpCap main toolbar. Press it to start the Occultation Manager.
<img width="117" height="28" alt="image" src="https://github.com/user-attachments/assets/6dbdf7af-aea5-4637-a39a-ff8a435dce55" />


