# Occultation Manager

SharpCap Occulation Manager for Occult Watcher Cloud
SharpCap Occultation Manager for Occult Watcher is a tool for SharpCap that fully automates occultation observations. It downloads personal observations announced in Occult Watcher Cloud. It includes an Event Manager to manage events, Sequence generation to create SharpCap sequences for doing the recordings (either in the tool itself or by using the sequences directly), and configuration management.

## The tool serves several purposes:

1. Enables full automation of observations from SharpCap, only requiring the use of OW Cloud to announce stations
2. Provides a much simplified work-flow for SharpCap users - other tools usually require the use of Occult Watcher Desktop or Occult 4 to generate or manage predictions, with a lot of manual work to select and run the observations, even with the OWD SharpCap addins
3. Provides a very easy and flexible way to generate SharpCap sequences to record events, with the ability for the user to edit the sequence template to their needs or edit the generate sequences

## How to Install the SharpCap Addin
1. Download the Python code from **occultation-manager.zip** above by right clicking and selecting 'Save As'
2. Unzip to a file locaiton where you have read/write access. Suggest a new subfolder  \Documents\Sharpcap\occultation-manager
3. Alternative, you could clone this GitHub respository if you are a GitHub user
4. Start SharpCap
5. In "File" - "SharpCap Settings" - "Startup Scripts" - find that folder and add the 'main' script

<img width="666" height="155" alt="image" src="https://github.com/user-attachments/assets/42a9d9c9-4273-4a88-8d0a-428cca649afe" />

5. Close SharpCap (the script will be loaded at the next start)

A new button should appear in the SharpCap main toolbar. Press it to start the Occultation Manager.
<img width="117" height="28" alt="image" src="https://github.com/user-attachments/assets/6dbdf7af-aea5-4637-a39a-ff8a435dce55" />

## Configuration Setup

Press the  Occultations button in SharpCap to start the Occultation Manager.

Setup your Occult Watcher Cloud configuration. Go to the **Tools | Configuration** menu, **Credentials** Tab and follow the instructions there. You will need an OWC account and API key.

Under the **File Paths** tab you can set file paths and file names. Default values should be fine but you might want to use a different folder for your Sequences.

Under **User Settings** set it up to suit your telescope following the instructions there.

Save the configuration.

## Sequencer Templates
The Occultation Manager is used to generate SharpCap Sequences, and these sequences are used to run the events. By using SharpCap Sequences the user can customise the event recording to their system and to what they need to do. So you can do anything that a SharpCap Sequence can do and automate as little or as much as you want. You can generate a single sequence that will run an entire nights observations.

The Local Time template is a fully working example for the Authors setup. It fully configures the mount and camera for each observation (binning, ROI, file format etc) and leaves the mount in a safe position after each observation. 

The Minimal template is a minimalist example. It assumes that you have already set up your camera and recording settings for how you want to record and only adjusts the exposure.

You will need to test these templates and adapt them to your setup and to how you want to record. My advice is to use something like the Local Time Template which sets all the camera parameters as it is really easy to forget to set something manually and then mess up the observation.

You will need to extensively test your own template(s) before trusting them of before they are safe to use for unattended observations. THere is the risk of failure, and the risk of damaging gear by snagging cables of leaving it pointed to the sun after sunrise.

