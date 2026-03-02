# OBS.XML Format Reference (Source Copy)

## Status Note (2026-03)

This file is a source-format reference copy used for export semantics and terminology checks.

Format for Asteroid Occultation Observations
Version 2.15+
XML format
Change log
V1.0 - Added Hourly rate of change of parallax (dParallax) to <Asteroid>. Changed file name to Asteroid~Observations.xml. Introduced Version number as a field in the file 
V1.1- Added <MainAtConjunction> and <SecondaryAtConjunction> 
V2.0 - multiple changes in the <star> line and <astrometry> lines. See Revision details for v4.10.0.0 of 22 March 2020 
V2.1 - added a field in the 'Position for an unseen primary of a binary asteroid' to <MainBody> 
V2.2 - added diameter uncertainties to <asteroid> 
V2.3 - To <Astrometry><MainBody> added fields for 'Fit Code', adjustments to along and across path uncertainty (x2) and Maximum/Minimum chord distances (x4). In <Satellite>, corrected the  of the units for the rates of motions 
V2.4 - Added new line <StarIssues> to include maters relating to the reliability of the Gaia star position. (RUWE, DuplicateSource flag, lack of proper motion, and where UCAC4 has been used to create a proper motion for the Gaia position  Expanded the <Prediction> line to add a field for Fee text. In <EllipticFit> Added new field for 'Future Review'. 
V2.5 - Added offset of the Center of Mass from the Center of Figure fit. - at end of the <EllipticFit> line. 
         - Added a new event code 'N' for events involving a ring - in Observations><Observer><D>, and ...<R> (July 2021) 
         - Added a new telescope type - eVscope 
V2.6 - Added offsets from the star position to the position of the star used for the solution, plus ratio of component brightness, in <Star><StarIssues>(April 2022) 
         - Expanded the list of fit options for shape models, to include 'Not constrained'. 
V2.7  - Added a new event code 'n' for non-detection of events involving a ring - in Observations><Observer><D>, and ...<R> . Also revised the definitions of M and m to replace all references to 'Miss' with 'non-detection' (October 2022) 
V2.8 - No change to the field definitions or content. Occult 4.2023.4.25 incorporated a major change associated with the numbering of ISAM shape models, and the consequential ability to only use models from ISAM that are not in DAMIT. The version change is used to ensure compatibility between the file content and the Occult handling of ISAM models. 
V2.9 - Added an extra category under <EllipticFit> for the item FitQuality, to accommodate a setting for single-frame events where astrometry will not be reported. (November 2023). Changed the telescope type descriptor under <Observations><Observer><ID> from the commercial identifier of 'eVscope' to the commercially neutral identifier of  'Electronic', with the qualifier '[intended to refer to small-aperture self-aligning telescopes with an electronic detector]'. (January 2024) 
V2.10 - Added an extra category under <EllipticFit> for the item FitQuality, to cover the situation where the occultation was of one component of a double star  'Only 1* of a double. No astrometry'.  Under <Astrometry><ReferenceTime>Added AcrossPath Uncertainty - due to Earth's rotation during reference time uncertainty (2024 May 5) 
V2.11 - Added a field under <MPC>  for the MPC Observation ID of an observation (2024 Dec 16) 
V2.12 - Added an extra category under <Doubles> to provide a date of submission of double data to the JDSO, and for the issue of publication   <JDSO> Date of submission | JDSO reference</JDSO>  (2025 Mar 03) 
V2.13 - Added an extra category under <Satellite> to provide the CBET number announcing the occultation discovery (2025 May 23) 
V2.14 - Added a field for the component ID of a known double star, under <StarIssues>   (2025 Aug 02 ) 
V2.15 - Changed tag at start and end of the file to be <AsteroidOccultations> and </AsteroidOccultations>  [to remove a long-standing unintended duplication in the use of the Tag <Observations>, which is used to embrace the lines for the details for all observers] (2025 Aug 22) 
 

The structure of the xml file is:
<AsteroidOccultations>
   <FileVersion>file version number</FileVersion>
   <Event>
        <Date> year| month| day| hour</Date>
        <Details>
           <Star> Catalogue| number| Gaia version|Gaia id| RA2000 (hh.hhhhhhhhhh)| Dec2000 (±dd.ddddddddd)|RA uncertainty (mas)|Dec uncertainty (mas)|Stellar diameter (mas)|IssuesFlag| RA Apparent (hh.hhhhhhhh)| Dec Apparent(±dd.ddddddd)|Mb|Mg|Mr| EPIC ID</Star>

               <StarIssues>Reliability|Gaia Duplicated Source flag|No Proper Motion flag|Proper motion using UCAC4|Double star solution - star brightness ratio|Uncertainty in the star brightness ratio, in percent|Double star solution RA offset (mas)| Double star solution Dec offset (mas)|Standard Deviation RA offset (mas)| Standard Deviation Dec offset (mas)|known double star component ID</StarIssues>
           <Asteroid> Number| Name| dX| dY| d2X| d2Y d3X| d3Y| Parallax| dParallax| Nominal mean diameter (km)|Uncertainty in mean diameter (km)| Mv</Asteroid>
           <EventFits>
              <SolveFlags>X| Y| Major Axis|  Minor Axis| PA Major Axis| Circular solution| Include Miss events| Separation of 2nd star/asteroid moon| PA of 2nd star/asteroid moon</SolveFlags>
              <EllipticFit>X| Y| Major axis| Minor Axis| PA Major Axis| Fit quality| Used Assumed Diameter| Flag for future review|Center of Mass X| Center of Mass Y</EllipticFit>
              <EllipseUncertainty>Sdev_X| Sdev_Y| SdevMajor| SdevMinor| SdevPA</EllipseUncertainty>
              <ShapeModelFit>
                 <Fit>Source| ID| SurfaceDia/VolumeDia ratio| Fit quality| Phase correction| Volume Dia Min| Volume Dia Max| Version</Fit>
                 .....
              </ShapeModelFit>
              <SatelliteFit>
                  <Satellite>IAU designation|SatdX|SatdY|Satd2X|Satd2Y|Separation|J2000 Position Angle|Uncertainty in separation|Uncertainty in Position angle| Major axis| Minor Axis| PA Major Axis| Fit quality</Satellite>
                  ....
              </SatelliteFit>
              <DoubleStar> 
                  <JDSO>Date of submission to the JDSO| JDSO publication reference </JDSO>
                  <Solution>PA| Separation| sdev_PA| Sdev_Separation| Centre_X| Centre_Y| Offset_X| Offset_Y| Solution number</Solution>
                  ...{either 1| 2 or 4 lines| depending on the nature of the solution}
              </DoubleStar>
           </EventFits>
           <Astrometry>
               <ReferenceTime>year| month| day|Reference hour|Uncertainty|AcrossPathUncertainty</ReferenceTime>
               <MainBody>IAU designation|GeocentricX| GeocentricY|dRACosDec|dDec|UncertRA|UncertDec| Position centered on shape model|number of chords used|Position for an unseen primary of a binary asteroid|Fit code|Adustment to the across path uncertainty|adjustment to the along path uncertainty|Maximum +'ve Hit chord distance|Maximum -'ve chord distance|Minimum +'ve Miss chord distance|Minimum -'ve chord distance</MainBody>
               <MainAtConjunction>IAU designation|GeocentricX at conjunction|GeocentricY at conjunction|Position for an unseen primary of a binary asteroid</MainAtConjunction>
               <SatelliteBodies>
                  <Secondary>IAU designation|GeocentricX| GeocentricY|PA_2000|dRACosDec|dDec|UncertRA|UncertDec|number of chords used</Secondary>
                  <SecondaryAtConjunction>IAU designation|MiriadeMotions|GeocentricX| GeocentricY|Year|Month| Day of conjunction|Sdev_day|Sdev_AlongTrack|Separation|Sdev_Separation|PAatConjuncton</SecondaryAtConjunction>
                   ...}
                   ...}
               </SatelliteBodies>
               <MPC>Date of publication|Circular number|MPC Submission ID</MPC>
           </Astrometry>
       </Details>
       <Observations>
           <Prediction>Seq Num|Longitude| Latitude| hr| min| sec|Event comments</Prediction>
           <Observer>
               <ID>Seq Num| Observer1| Observer2| MoreThan2Observers| NearLocation| State/country| Longitude| Latitude| Alt| Datum| TelescopeAperture| TelescopeType| Observing method| Time Source</ID> 
               <Conditions>Stability| Transparency| SN| Time Adjustment| Comment</Conditions>
               <D>hh mm ss.ss| eventCode| Accuracy| PEqn| Weight| PlotCode</D>
               <R>hh mm ss.ss| eventCode| Accuracy| PEqn| Weight| PlotCode</R> 
           </Observer>
           ...
        </Observations>
        <Added> yyyy|m|d</Added>
        <LastEdited>yyyy|m|d</LastEdited>
   </Event>
</AsteroidOccultations>

The tag <AsteroidOccultations> delimits the XML file

The tag <FileVersion> specifies a version number for the file format. The number is a decimal number, and is used to identify the need to upgrade either the file, or the version of Occult.

The tag <Event> delimits the data for an event. The whole file will be read into memory, but only data within an event will be decoded (when required).

Within an event, the tags <ShapeModelFit>, <DoubleStar> and <BinaryAsteroid> will only be present when appropriate, as will three items under <Astrometry>

Within a data element, individual items are stored as pipe-separated-values. This allows commas to be used in several fields.

IMPORTANT. None of the data items have been corrected for the Gaia DR3 Frame Rotation error. This correction is only applied when generating astrometric outputs.

 

Tag Data items 
Date Date of the event

The year, month, and day of the event, and the hour (to 0.1 hrs) close to the observed event times. If observations extend across different days, specify the earlier day, with times going above 24hrs as required. 
 
Star Details of the star

Catalogue - the catalogue identifier. The identifiers used are:
HIP (Hipparcos), Tycho2 (or TYC), UCAC4, USNO-B1, NOMAD and G-coords 
Number - the number in the catalogue 
Gaia version - The source of the star position. 0 = Hipparcos2, 1 = Gaia DR1, 2 = Gaia DR2, 3 = Gaia EDR3, 9 = USNO Bright Star Catalogue (UBSC, 2022), -1 = not specified 
Gaia id - the 18-digit Gaia id in the relevant Gaia version 
Right Ascension (hh.hhhhhhhhhh - the RA of the star. GCRS coordinates. (That is, coordinates referred to the ICRS reference frame of 2000, proper motion to date, corrected for parallax). No correction for relativistic light bending. 
Declination (±dd.ddddddddd) - the Declination of the star, GCRS coordinates. No correction for relativistic light bending. 
Uncertainty in Right Ascension (mas) - incorporating position, proper motion and parallax uncertainties 
Uncertainty in Declination (mas) - incorporating position, proper motion and parallax uncertainties 
Angular diameter of star (mas) - using the Gaia estimated star diameter from DR2. For stars added after the beginning of 2021, an estimate based on the star’s magnitudes is given as the quantity is not available in EDR3. 
Issues flag. 0 = no issues, 1 = high RUWE,  2 = Duplicate source flag, 3 = 1 + 2.
- see Notes for explanations 
Right Ascension - apparent, hh.hhhhhhhh. The apparent RA of the star at the Date+time of the event, with no correction for relativistic light bending. 
Declination - apparent (±dd.ddddddd) The apparent declination of the star at the Date+time of the event, with no correction for relativistic light bending. 
Mb - The Gaia blue magnitude of the star 
Mg - The Gaia G magnitude. For non-Gaia stars, the V magnitude 
Mr - The Gaia red magnitude of the star. Where available, the Red Photometer magnitude of Gaia 
EPIC ID - the identification of stars if they are observed in the Keplar2 mission 
 
StarIssues Extra details about the star

Reliability. A measure of whether the star position is fully reliable. 
For Gaia stars, the value is the RUWE (Renormalised Unit Weight Error). "The RUWE is expected to be around 1.0 for sources where the single-star model provides a good fit to the astrometric observations. A value significantly greater than 1.0 (say, >1.4) could indicate that the source is non-single or otherwise problematic for the astrometric solution." 
For star positions sourced from TychoGaia: the 'astrometric-excess-noise' parameter 
For star positions sourced from Hipparcos2: a value computed using the Hipparcos values of Ntr, F2, and the number of parameters in the solution. The result is largely equivalent to RUWE. 
Duplicated Source flag. A flag in Gaia. 0 = not set, 1 = set, -1 = not specified (that is, position comes from TychoGaia or Hipparcos2)
During data processing, this source happened to be duplicated and only one source identifier has been kept. Observations assigned to the discarded source identifier(s) were not used. This may indicate observational, cross-matching or processing problems, or stellar multiplicity, and probable astrometric or photometric problems in all cases. In Gaia DR1 and DR2, for close doubles with separations below some 2 arcsec, truncated windows have not been processed, neither in astrometry nor photometry. The transmitted window is centred on the brighter part of the acquired window, so the brighter component has a better chance to be selected, even when processing the fainter transit. If more than two images are contained in a window, the result of the image parameter determination is unpredictable in the sense that it might refer to either (or neither) image, and no consistency is assured. 

No proper motion  flag. Indicates that no proper motion has been specified in the Gaia catalogue. Values are 0 = has proper motion, 1 = no proper motion, -1 = not specified (that is, position comes from TychoGaia or Hipparcos2, which will have proper motions). An RUWE of 0 appears to be applied when there is no proper motion in Gaia. 
Proper motion derived using UCAC4. For some stars where there is no proper motion in Gaia, and approximate proper motion was added by comparing the UCAC4 J2000 position with the Gaia 2016 position. Values are 0 = (includes stars with Gaia proper motions, or stars with no Gaia proper motions that were not matched to UCAC4), 1 = proper motion added,  -1 = not specified (that is, the position comes from TychoGaia or Hipparcos2) 
Double star - ratio of star brightness. Default is 1.2. The ratio is used to determine to location of the Gaia position along the component separation. If R is the ratio (reference/other), the distance of the reference star from the Gaia position is Separation/(R + 1) 
Uncertainty in the star brightness ratio, as %. Default is 10 
Double star solution, offset in RA. The offset in RA from the Gaia position, of the component used for the occultation solution. 
Double star solution, offset in Dec. The offset in Dec from the Gaia position, of the component used for the occultation solution. 
Double star solution, Standard deviation in offset in RA. 
Double star solution, Standard deviation in offset in Dec. 
Double star solution. If the star, is a known component of a double star at the date of the observation, that known pairing.  
 
Asteroid  Details of the asteroid

Number - the number of the asteroid 
Name - the asteroid's name, or other identification [the name of asteroid (229762) G!kun||'homdima is held as Gunhoumdima] 
Positions on the Apparent fundamental plane are computed using orbital elements at the Date + time of the event, with the shadow motion being expressed as
 a*T + b*T2 + c*T3 ,
where T is the time (in hours) from the hour under Date. The following give the coefficients for this expression. 
dX - coefficient 'a' in X (Earth radii/hr) 
dY - coefficient 'a' in Y (Earth radii//hr) 
d2X - coefficient 'b' in X (Earth radii/hr2) 
d2Y - coefficient 'b' in Y (Earth radii/hr2) 
d3X - coefficient 'c' in X (Earth radii/hr3) 
d3Y - coefficient 'c' in Y (Earth radii/hr3) 


Parallax - in arcsec, at the hour under Date 
dParallax - in arcsec. The hourly rate of change in parallax

Nominal mean diameter - in km. Typically from IR satellite measurements 
Uncertainty in that diameter - km (added in v2.2) 
Mv - the Visual magnitude of the asteroid 
 
SolveFlags Flags for automatic fitting

A number of parameters can be set for automatic fitting - and this is indicated by a flag. The flag is:
0 if the parameter has not been included in the automatic fitting
1 if the parameter was included in the automatic fitting of an ellipse to observed chords
The parameters for which the flags are set are: 
X coordinate 
Y coordinate 
Major Axis 
Minor Axis 
PA Major Axis 
Circular solution 
Include Miss events 
Separation of 2nd star/asteroid moon 
PA of 2nd star/asteroid moon 
 
EllipticFit Details of the fit of an ellipse to the observed chords

X - X-coordinate of the center of the best-fit ellipse (in km) relative to the reference frame used to plot the observations 
Y - Y-coordinate of the center of the best-fit ellipse (in km) relative to the reference frame used to plot the observations 
Major axis - in km 
Minor Axis - in km 
PA Major Axis - in deg 
Fit quality - a code indicating the quality of the fit 
0 = 'No reliable position or size'
1= 'Astrometry only. No reliable size' Observation can be used to report astrometry, but nothing meaningful about the asteroid's size.
2 = 'Limits on size, but no shape'. Poor coverage around the profile, but a diameter is determinable (often with a fit to a shape model)
3 = 'Reliable size. Can fit to shape models'. Good coverage around much of the profile enabling a reliable determination of the asteroid's size - even without a shape model 
4 = 'Resolution better than shape models'. Profile of the asteroid well covered with highly consistent results
5 = 'Short duration event. No astrometry'. For events where there is only one positive chord, and the duration of the potential occultation is for one or two video frames or camera exposures. Such events are not used for any reporting process; it is provided only as a holding place. 
6 = 'Only 1* of a double. No astrometry'. For events where the observed light drop was clearly less than the expected drop, and could not be explained by variation in the brightness of the asteroid - leaving the only explanation being the occultation was one component of a double star, with the other component not detected. No astrometry because the location of the photocenter to match the Gaia star position cannot be determined.

Used Assumed Diameter - flag to indicate the major/minor axes are assumed values (e.g. from IR satellite measures) rather than derived from the observation. 
Flag to indicate the event should be reviewed in the future because of particular issues that might be resolved with further information (0 = false, 1 = true) 
X-offset from X to the Center of Mass location - in km 
Y-offset from Y to the Center of Mass location - in km 
 
EllipseUncertainty The standard deviations of the values for the fitted ellipse

X - X-coordinate of the center of the best-fit ellipse relative to the reference frame used to plot the observations (km) 
Y - Y-coordinate of the center of the best-fit ellipse relative to the reference frame used to plot the observations (km) 
Major axis - in km 
Minor Axis - in km 
PA Major Axis - in deg 
 
ShapeModelFit Where shape models are available, this group gives data about the fits to shape models

Each shape model has its own group with the tags <Fit>  </Fit>. The items within each such group are: 
Source  - The shape model source name (DAMIT, ISAM) 
ID - the identification within that source 
SurfaceDia/VolumeDia ratio - the ratio of the Surface-equivalent diameter to the Volume-equivalent diameter of the shape model. 
Fit quality - a flag to indicate whether the model is consistent with the occultation observations.
0 = Not fitted. Too few chords to make a fit to the shape model.
1 = Bad occn data. The occultation observations are either inconsistent or unreliable, with no ready way of distinguishing between reliable and unreliable observations
2 = Model wrong. The shape model is clearly inconsistent with the observed chords
3 = Minimum Dia. Usually associated with a single chord observation, with that chord being matched to the largest dimension of the shape model to give its minimum diameter
4 = Diameter but no fit. The chords do not sensibly match the shape model, yet it is possible to derive minimum and maximum possible diameters. [NOTE: flag 1 - Model wrong - should be used unless there is a degree of confidence that the derived diameters are 'in the right ball-park']
5 = Poor fit. The shape model is generally consistent with the observed chords - but has some broad deviations
6 = Good fit. The shape model has a high degree of correspondence with the observed chords.
7 = Not constrained. The observations have been compared to the shape model, but the distribution of the chords, or the magnitude of the uncertainties, were such that no meaningful constraints could be determined. Setting 7 added with effect from May 2022 
Phase correction - the rotational correction (in degrees) applied to optimize the fit. Only applied if the light curve data warrants such an adjustment. 
Volume Dia Min - the minimum volume-equivalent diameter arising from a fit of the chords to the shape model 
Volume Dia Max - the maximum volume-equivalent diameter arising from a fit of the chords to the shape model 
Version - information about the version 
 
Satellite Details of an observed companion to an asteroid

This group only appears if the observation shows the presence of two  bodies. 
As at 2019, the fit to the satellite is 'manual', so there are no determined standard deviation values
IAU designation of companion 
Sat_dRA - motion of the satellite in Right Ascension relative to the system's center of mass. Units are mas/hr. The zero time is same as for the motions of the main body. [Note this and the following three items are only set if a Miriade ephemeris is available for the system. Otherwise the values are set to zero. These values are only used to align the chords of the satellite.] 
Sat_dDec - motion in Declination relative to the system's center of mass 
Sat_d2RA - 2nd order motion in  Right Ascension relative to the system's center of mass 
Sat_d2Dec - 2nd order motion in Declination relative to the system's center of mass 
Separation (mas) 
PA (deg) PA of companion with respect to the main body - Apparent reference frame 
Uncertainty in Separation (mas) 
Uncertainty in PA 
Major axis (km) - of the companion 
Minor Axis (km) - of the companion 
PA Major Axis  (Deg) - of the companion 
Fit quality
None    No fit to the satellite. This is only used when the observations indicate the detection of a satellite, but the observations have not been analyzed to obtain a fit to the observations. 
Is it a satellite?   The observations indicates the possibility of a satellite. However the observational evidence is not sufficient to assert a definite detection. [Single-chord visual observations would typically fall into this category, as well as single noisy video recordings] 
Approx offset   The existence of a satellite is reasonably definite. The approximate location of the satellite can be determined, but not its size or shape 
Offset + size   An accurate location location of the satellite is determined, together with a size derived by assuming it is spherical 
Offset + shape   An accurate determination of the location, size and shape of the satellite. 
CBET number announcing the occultation discovery 

 
DoubleStar Details of double star solutions

This group only appears if the observation indicates the star is double.

The number of times this line can appear depends on the circumstances of the event, as follows:
1 - if there are two or more spaced chords for both the primary and secondary star, such that there is no doubt about which side of the asteroid the primary or secondary star passed as seen by the observers. This provides a unique solution.

2 - if there are two or more spaced chords for one component of the pair - such that there is no doubt about which side of the asteroid that component passed. However if the other component does not have sufficient chords to determine which side of the asteroid it passed, there are two possible solutions.

4 - if the number of observed chords is insufficient to locate either component against one or other side of the asteroid, leading to 4 possible solutions. This situation most commonly occurs with single-chord events, but it also occurs when there are two or more chords which happen to be closely spaced such that the relevant side of the asteroid cannot be determined.

Tag Data items 
JDSO Publication in Journal of Double Star Observations 
Date of submission to the JDSO
JDSO publication reference - Volume/Issue/Page
 
Solution The double star solution, or one of multiple double star solutions.

This group is repeated as often as required - 1, 2 or 4 times. 
PA - the PA of the companion (deg) 
Separation - the separation of the components (mas)    * may be negative: see note below 
Uncertainty in PA 
Uncertainty in Separation 
Centre in X - for when there are plural solutions 
Centre in Y - for when there are plural solutions 
Offset in X 
Offset in Y 
Solution number 
The Offsets in X and Y apply when there are insufficient chords to locate the primary star on one side or the other of the asteroid. In this situation there are 4 potential solutions:
* primary star on one side of the asteroid, with secondary on one or the other side; and
* primary star on other side of asteroid, with secondary on one or the other side.
The offset value places the primary star one one or other side of the asteroid, avoiding the need to re-solve for the position of the asteroid. The astrometric position is for the mean relative location of the primary star.

Where the occultation is of one star only of a double star (demonstrated by the light drop being significantly less than expected, the Separation is specified as a negative value 


 
Astrometry Details of the astrometric solution derived from the event

This group only appears if the quality setting under EllipticFit is greater than 0.

There are three groups under this heading:
Tag Data Items 
ReferenceTime The time used for reporting an event. 
If the event involves a satellite, this time is the average of all events involving the satellite that have been used in the solution. This time is used for both the satellite, and the primary body.

If the star is a double star, only the primary events are used. The first step in the solution is to identify the location of the center of the asteroid relative to the geocenter, at a time identified by a particular observed event that is used to define the plot axes. 
Year  (yyyy) 
Month (mm) 
Day (dd) 
Reference hour (hh.hhhhhh) 
Uncertainty in the reference time (s.sss) (including  effect of earth's rotation during uncertainty period) 
Across Path Uncertainty (mas)  (arising from earth's rotation during uncertainty period) 
 
MainBody Event details at the Reference Time

IAU designation 
FundamentalPlaneX (km)  kkkk.k (apparent) 
FundamentalPlaneY (km)  kkkk.k (apparent) 
dRACosDec  (arcsec) - J2000 
dDec (arcsec) - J2000 
UncertRA (arcsec)  - uncertainty in Time included. This data element is not used. Final RA uncertainty is based on along/across track uncertainties and time uncertainty. 
UncertDec (arcsec) - uncertainty in Time included. This data element is not used. Final Dec uncertainty is based on along/across track uncertainties and time uncertainty. 
Position centered on shape model (0=false, 1=true). Set to false if <EllipticFit>, X-offset or Y-Offset, are non-zero 
number of chords used 
Position is for an unseen primary of a binary asteroid
(0=false, 1=true), and is used solely as the origin for the position of the satellite.

The values of dRACosDec and dDec are 'observed' values. They have been converted from the Apparent reference frame to J2000. They have not had the effects of deflection of the asteroid relative to the star removed.
Fit code - uncertainty in position of center of asteroid. 
Parts of the Error Code use the following 5 parameters, which relate to the distance of certain chords on either side of the center of the asteroid. In these parameters, the side of the path is indicated as Plus, or Minus - with Plus referring to the north-side of the path. Hit refers to positive occultation events, while Miss refers to Miss events. The Hit parameters specify the distance of the furthest positive chord on either side of the path, with a value of zero if there is no such chord on the particular side. The Miss parameters specify the distance of the closest Miss chord on either side of the path, with a value of +9 or -9 if there is no such chord on the particular side. The distances are expressed in units of the asteroid's assumed radius.
: 
Well-located : PlusHit >= 0.3 and MinusHit <= -0.3 
Poorly-Located : (PlusHit - MinusHit) > 0.5, with either PlusHit < 0.3 or MinusHit > -0.3 
Constrained : either PlusMiss < 1.3 or MinusMiss > -1.3
Unconstrained : none of the above
MeanLocation :the Absolute Value of the average of PlusHit and MinusHit - with the MeanLocation value limited to between +0.2 and +0.8.
The fit uncertainty categories are:

a - the uncertainty is that from a least squares fit of an unrestricted ellipse to the observed chords. This provides the minimal value of the uncertainties. (a) is usually replaced by one of the following codes. However it will appear for occultations by the major planets and larger planetary satellites, when they have a known diameter and are known to be spherical.


b - For asteroids only. If the astrometric position is set to match the _center_ of a shape model (center of mass solution) - the uncertainties for both the Along-Path and Across-Path directions are set at 5% of the assumed diameter.


c - if not b, but has a shape model fit of either 'poor' or 'good' 
c1 - If the overall event quality is 'Reliable Size...' or 'Resolution better than Shape models': uncertainties for both the Along-Path and Across-Path directions are set at 8% of the assumed diameter.
c2 - If the overall event quality is 'Limits on size, but no shape': uncertainties for both the Along-Path and Across-Path directions are set at 12% of the assumed diameter.


(d) - for major planets & their large moons. This relies on they being essentially circular in profile, and their diameters being accurately known - to provide good astrometry in circumstances which would not apply to asteroids. 
d1 - if Well-located: uncertainties of (a), unchanged 
d2 - if Poorly-located: three times the uncertainties of (a) 4% of assumed diameter
d3 - if Constrained:
(i) if only 1 chord, or the spread of the chords is less than 5% of the assumed diameter,
if the motion in the time uncertainty period is greater than the Along-Path uncertainty, that motion distance is taken as the Along-Path uncertainty. The Along-Path and Across-Path uncertainties are taken as this value.
otherwise the Along-Path and Across-Path uncertainties are the uncertainties from the fit
(ii) if not (i), the Along-Path and Across-Path are the uncertainties from the fit.
** For both (i) and (ii): The Across-Path uncertainty is divided by the MeanLocation value, and the Along-path uncertainty is divided by SQRT(1- MeanLocation^2)
d4 - if Not-constrained:
(i) If only one chord, 
the Along-Path uncertainty is computed on the same basis as for  'd3 - if Constrained', (i), first dot point. 
if the chord is located more than 2 arc-seconds from the center of the object, the Across-Path uncertainty is computed on the same basis as for 'd3 - if Constrained', (i), first dot point. 
Otherwise the Across-Path uncertainty is set as 25% of the object's assumed diameter 
(ii) If more than one chord
the Along-Path uncertainty is computed on the same basis as for 'd3 - if Constrained', (i), second dot point.
if the MeanLocation value is greater than 25% of its assumed radius, AND (PlusHit - MinusHit) >0.05, 
OR the MeanLocation value is greater than 15% of its assumed radius, AND (PlusHit - MinusHit) >0.10, 
the Across-Path uncertainty is the uncertainty from the fit
otherwise the Across-Path uncertainty is set as 25% of the object's assumed diameter 
** For both (i) and (ii):  The Across-Path uncertainty from the first two dot points (but not the third) is divided by the MeanLocation value. The Along-path uncertainty is divided by SQRT(1- MeanLocation^2)


e - if (b), (c) and (d) do not apply: 
This applies to events where quality is better than 'Astrometry only', and either 
(i) the Major + Minor axes are included in the Least Squares solution, or 
(ii) the solution is for a circle.
The uncertainties are separately considered in the Along-Path and Across-Path directions, and are set as the larger of the uncertainty from (a), and the uncertainty specified in the relevant one of e1 to e8: 

If the overall event quality is 'Limits on size, but no shape' 
e1 - Well-located - uncertainty must be at least 8% of assumed diameter
e2 - Poorly-located - uncertainty must be at least 12% of assumed diameter
e3 - Constrained - uncertainty must be at least 16% of assumed diameter
e4 - Unconstrained - uncertainty must be at least 20% of assumed diameter


If the overall event quality is 'Reliable size', or 'Resolution better than Shape models'
e5 - Well-located - uncertainty must be at least 5% of assumed diameter
e6 - Poorly-located -uncertainty must be at least 8% of assumed diameter
e7 - Constrained - uncertainty must be at least 12% of assumed diameter
e8 - Unconstrained - uncertainty must be at least 16% of assumed diameter

f - if none of (b) to (e) apply: 
Across-Path uncertainty set on following basis: 
f1 - Well-located: the uncertainty in the assumed diameter of the asteroid.
f2 - Poorly-located: twice the uncertainty in the assumed diameter of the asteroid./span>
f3 - Constrained: twice the uncertainty in the assumed diameter of the asteroid (same as f2). 
f4 - Unconstrained: 40% of the assumed diameter of the asteroid.

Along-Path uncertainty for each of f1 to f4, is set on following basis: 
For each positive chord:: 
if chord length > 0.8 of assumed diameter - the Along-Path uncertainty for that chord is set at 5% of assumed diameter of the asteroid.
else if chord length > 0.6 of assumed diameter - the Along-Path uncertainty for that chord is set at 10% of assumed diameter of the asteroid.
Otherwise - the Along-Path uncertainty for that chord is set at 20% of assumed diameter of the asteroid.
Along-Path uncertainty set as the mean of the individual Along-Path uncertainties, assessed in inverse quadrature (to give greater significance to smaller uncertainty values).


The increase from codes (b) to (f) to the Across-Path uncertainty compared  to the uncertainty from (a) (km) 
The increase from codes (b) to (f) to the Along-Path uncertainty compared to the uncertainty from (a) (km) 
Maximum +'ve Hit distance, asteroid radii d.dd (always set) 
Maximum -'ve Hit distance, asteroid radii -d.dd (always set) 
Minimum +'ve Miss distance, asteroid radii d.dd; 9 = not set 
Maximum -'ve Miss distance, asteroid radii -d.d; -9 = not set
 
MainAt Conjunction Event details at for the time of Geocentric Conjunction

IAU designation 
GeocentricX  at Conjunction (km)  kkkk.k 
GeocentricY at Conjunction (km)  kkkk.k 
Year of Conjunction 
Month of Conjunction 
Day of Conjunction dd.ddddddd 
Standard Deviation in Time of Conjunction d.ddddddd 
Standard deviation Along-track (mas)  (s.s) - from fit only, SDev in Time of Conj not included 
Separation at conjunction (arcsec)  ss.ssss 
Standard deviation Across-track {Separation} (mas) (s.s) 
Position Angle of Conjunction (deg)  ddd.ddd 
Position is for an unseen primary of a binary asteroid
(0=false, 1=true), and is used solely as the origin for the position of the satellite 
The values are 'observed' values. They have been converted from the Apparent reference frame to J2000. They have not had the effects of deflection of the asteroid relative to the star removed.

 
Secondary Event details at the Reference Time

IAU designation 
GeocentricX (km)  kkkk.k 
GeocentricY (km)  kkkk.k 
PA (deg) PA of companion with respect to the main body - J2000 reference frame 
dRACosDec (arcsec) 
dDec (arcsec) 
UncertRA (arcsec) 
UncertDec (arcsec) 
number of chords used 

The values of dRACosDec and dDec are 'observed' values, They have been converted from the Apparent reference frame to J2000. They have not had the effects of deflection of the satellite relative to the star removed.

 
SecondaryAt Conjunction Event details at for the time of Geocentric Conjunction

IAU designation 
Satellite motions (from Miriade) allowed for in the solution. 0 = no, 1 = yes 
GeocentricX  at Conjunction (km)  kkkk.k 
GeocentricY at Conjunction (km)  kkkk.k 
Year of Conjunction 
Month of Conjunction 
Day of Conjunction dd.ddddddd 
Standard Deviation in Time of Conjunction d.ddddddd 
Standard deviation Along-track (mas)  (s.s) 
Separation at conjunction (arcsec)  ss.ssss 
Standard deviation Across-track {Separation} (mas) (s.s) 
Position Angle of Conjunction (deg)  ddd.ddd 
The values are 'observed' values. They have been converted from the Apparent reference frame to J2000. They have not had the effects of deflection of the asteroid relative to the star removed.

 
MPC Details of publication by the Minor Planet Center 
Date of submitting the accepted observation to the MPC 
MPC Circular number of the summary report 
MPC Observation ID 
 

 
Observations This provides a series of groups giving details for each observer

There are two groups under this heading.

Tag Data items 
Prediction Details for a predicted central line location near the observed locations

The prediction information is used to validate the observed data, and to calculate the offset between prediction and observed 
Sequential reference number 
Prediction Longitude (±ddd mm ss.s) 
Prediction Latitude (±dd mm ss.s) 
Time (hh mm ss.s) The time is always positive. For events near 0hrs UT, the hour can be 24 or more 
Event comments. A free-text field for overall comments about the event - such as why no astrometry is reported. Field added at start of 2021 - and is incomplete for earlier years. From Nov 2021, field includes the source of the orbit used for the prediction in this tag. 
 
Observer Observer details.

This group is repeated as often as required

There are four groups under this heading. 

Tag Data Item 
ID Details of the observer and equipment 
Sequential reference number 
Name 1 
Name 2 
More Than 2 observers 
located near 
State or country (2 or 3 letter code) 
Longitude   (±ddd mm ss.s) 
Latitude    (±dd mm ss.ss) 
Alt  (m) 
Datum
_ = WGS84 
N = NAD1927
E = ED1950
T = Tokyo
G = GB1936
* = unspecified, or other. 
Telescope Aperture (cm) 
Telescope Type
_ = unstated
1 = Refractor
2 = Newtonian
3 = SCT
4 = Dobsonian
5 = Binoculars
6 = Other
7 = None
8 = Electronic [intended to refer to small-aperture self-aligning telescopes with an electronic detector] 
Observing method
    unspecified
a  Analogue & digital video
b  Digital SLR-camera video
c  Photometer
d  Sequential images
e  Drift scan
f   Visual
g  Other

Time Source
   unspecified
a GPS
b NTP
c Telephone (fixed or mobile)
d Radio time signal
e Internal clock of recorder [such as by calibrating the recorder well before and after the event]
f  Stopwatch
g Other

 
Conditions Observing Conditions 
Stability
_ = unstated
1 = Steady
2 = Slight flickering
3 = Strong flickering 
Transparency
_ = unstated
1 = Clear
2 = Fog
3 = Thin cloud <2 [mag loss <2 mag.]
4 = Thick cloud >2 [mag loss >2 mag. 
5 = Broken opaque cloud [that is, observed thru gaps in the cloud]
6 = Star faint
7 = By averted vision 
SN 
Time Adjustment  (±s.ss) [Adjustment to time base of observer, to fit to other observations ] 
Free-text comments 
 
D Details of the D event 
hh mm ss.ss.   Always +'ve values. For events near 0hrs UT, the hour can be 24h or more 
event Code 
D for main star
d for 2nd star
G for satellite with main star
g for satellite with 2nd star
M applies to situations where an occultation event could not be reliably detected. Most commonly this relates to a situation where the object did not occult the star. However there may be other explanations for the non-detection.
m applies to situations where an occultation event involving a 2nd star of a double star could not be reliably detected. Most commonly this relates to a situation where the object did not occult the 2nd star. However there may be other explanations for the non-detection.
N for events involving a ring. The D and R times are for opposite arms of a ring. Where there is a D+R for an arm of a ring, the mid-time is specified, with the duration being given in FREE_TEXT
n for asteroids (or planets) known to have one or more rings, and an occultation by that ring(s) could not be reliably detected. Most commonly this relates to the star not crossing the orbit of any ring, or the absence of material in the portion of a ring crossed by the star. However there may be other explanations for the non-detection.
C for Not Seen - e.g. because of cloud
e for an artificial D time of the primary body of an asteroid with satellites - for use when the primary component is not observed. Always a predicted location and time. 
Accuracy (s.ss) [usually specified by the observer. See below for default values when not specified.] 
PEqn (s.s) 
Weight  [Usually set as 'blank'. See below for default values that are then applied] 
Include in Solution Code 
_ Include observation
x Exclude observation
y Include D only
z Include R only 
 
R Details of the R event 
hh mm ss.ss.   Always +'ve values. For events near 0hrs UT, the hour can be 24h or more 
event Code
R for main star
r for 2nd star
B for satellite with main star
b for satellite with 2nd star
M applies to situations where an occultation event could not be reliably detected. Most commonly this relates to a situation where the object did not occult the star. However there may be other explanations for the non-detection.
m applies to situations where an occultation event involving a 2nd star of a double star could not be reliably detected. Most commonly this relates to a situation where the object did not occult the 2nd star. However there may be other explanations for the non-detection.
N for events involving a ring. The D and R times are for opposite arms of a ring. Where there is a D+R for an arm of a ring, the mid-time is specified, with the duration being given in FREE_TEXT
n for asteroids (or planets) known to have one or more rings, and an occultation by that ring(s) could not be reliably detected. Most commonly this relates to the star not crossing the orbit of any ring, or the absence of material in the portion of a ring crossed by the star. However there may be other explanations for the non-detection.
C for Not Seen - e.g. because of cloud. 
f for an artificial R time of the primary body of an asteroid with satellites - for use when the primary component is not observed. Usually a predicted location and time.
Accuracy (s.ss) [usually specified by the observer. See below for default values when not specified.] 
PEqn (s.s) 
Weight  [Usually set as blank. See below for default values that are then applied.] 
Include in Solution Code.
_ Include observation
x Exclude observation
y Include D only
z Include R only 
 
LightData Meta data for the light curve of the observation 
When the event is soon after 0hrs UT, the start of the light curve can be in the day preceding the date in the Date field above. Similarly, if the event time is greater than 24h, the start of the light curve can be in the day following the date in the Date field above. 

Year - for first data point 
Month - for first data point 
Day - for first data point 
Hr - for first data point 
Min - for first data point 
Sec - for first data point 
Duration - the time difference in seconds between the first and last data points in the light curve 
#Points - the number of data points in the light curve 
 
LightValues Light Curve values, as integers 
A series of values representing the light curve value. 
The values are scaled such that the maximum value is set to 9524 (=10,000/1.05). As a result, all light curve values have a maximum near to, but less than, 10000 - irrespective of the numeric values in the source light curve. (No adjustments to the zero-level in the light curve data are applied.)

Where the light curve is missing one or more exposures, the data element for that exposure is empty.

The number of elements is specified in #Points in LightData 
 


Some items have default values:
Accuracy is usually set by the observer. However when not set (which most commonly occurs for observations before 2000) the accuracy is set as follows: 
If the observing Method was 'a', 'b', or 'c' 
0.5 sec if the Time Source was 'a', 'd', 'e', 'f'; 
1.5 sec if the time source was 'b', 'c', or 'g' 
1.0 sec if the observing Method was 'd', 'e', 'f', or 'g' 
Weight is usually set as Blank. When solving for the best fit, the applied weights are:
5 - for analogue or digital (non-SLR) video
4 - for digital SLR-camera video, and Photometer
3 - for sequential images and drift scan
1 - for visual and anything else.
0 - event is ignored in any solution, but may still be plotted

Miss events are considered only if expressly included in the solution - in which case they are weighted 5.

Plot code - determines whether an event is plotted in Occult, and by corollary whether the event is reliable in any way. The settings are:
<blank> - both events plotted
x - neither event is plotted
y - only the D event plotted
z - only the R event plotted 
 
 
Added The date the record was added to the file 
LastEdited The date the record was last edited 
