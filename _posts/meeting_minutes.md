NineML working group meeting: Antwerp, 13 – 15 October 2015


Paticipants:
Erik De Schutter, Alex Cope, Tom Close, Andrew Davison, Pat Vermeiren, and Mathew Abrams


________________
Agenda
Day 1: Monday, 13 October 2014
19.00         Dinner: Holiday Inn Crowne Plaza Restaurant


Day 2: Tuesday, 14 October 2014
09.00 – 10.15 Prioritize discussion points 
10.15 – 10.45 Coffee Break
10.45 – 12.00 Discussion Session
12.00 – 13.00 Lunch
13.00 – 15.15 Discussion Session
15.15 – 15.45 Coffee Break
15.45 – 18.00 Discussion Session
19.00                  Dinner (Het Promphuis)


Day 3: Wednesday, 15 October 2014
09.00 – 10.15 Discussion Session
10.15 – 10.45 Coffee Break
10.45 – 12.00 Discussion Session
12.00 – 13.00 Lunch
13.00 – 14.15 Discussion Session
14.15 – 14.45 Coffee Break
14.45 – 17.00 Closing Session (discussion of future meetings and
                      the upkeep of NineML)
19.00              Dinner (a la ville)
________________


Summary 
On Day 1, the discussion points were prioritized according to what is required for version 1 of the specification (section A). The additional discussion points were organized into 2 categories: i. what will be required for version 2 of the specification (section B) and ii. what could be deferred to a later point in time (section C). The committee then systematically addressed all the discussion points considered critical for version 1 of the specification. During the afternoon of Day-2, the committee began to address some of the discussion points that are critical for version 2 of specification. At the conclusion of the meeting, all discussion points (version 1 of the specification, as well as some for version 2) that required action were assigned to committee members. The committee discussed future meetings and upkeep of NineML. It was decided tentative dates for the next in-person meeting for which the focus will be to complete version 2 of the specification--tentative dates: late March/early April and end of May/early June (Sheffield is the location if these dates are selected).



Discussion Point Prioritization/Actions

A. Version 1 Requirements/Actions
1. Moving “Property” elements outside of the “properties” tags in component elements--easy to agree--get rid of the property container--approved. Checked against xml schema.
2. Referencing components from separate files using a “reference” tag.-- see GitHub #26
3. Specify class name in definition link (and let the class define its own language)--depends on point 2--people agree on the notion
4. Specify units as an attribute of value tag instead of a separate tag --see github #24 for proposal--with units in “quantity”.have a recommended file format. 
5. Ports need explicit tag names for validation (python library, specification, and chicken scheme)--github#35--assigned to Tom 
6. Specification of sets (github#34)--chicken scheme, python library, and specification--format listed on the ticket. concatenate used instead of union. subsets deferred to version 2--see github #38--assigned to Tom
7. XML syntax for projections (python library, chicken scheme, and specification)--agreed on proposal #2 in github#33. It was decided that delays should probably be a property of port-connections (see code snippet), but this causes problems due to the need to specify identical values for  source→ response and sources-->plasticity connections, when those values come from an RNG. For version, we will specify the delay as a property of the Projection (and delay for any target-->plasticity connection is assumed to be zero). Handling more complex scenarios is postponed to v.2.--assigned to Tom
8. Moving “property” elements outside of the “properties” tags in component elements--assigned to Tom
9. Referencing components from separate files using a “reference tag (python library, specification, and chicken scheme)--assigned to Tom
10. Specify units as an attribute of value tag instead of separate tag (python library, specification, and chicken scheme)
11. Adding basic connectivity (github #21)--will speak to Mikael Djurfeldt about this--for version 1: for explicit data, allow 2 formats for connectivity data (csv, hdf5).  All data columns must be labeled uniquely, and they are then referred to in the explicits connections as presented in github #21. Binary file format still outstanding--assigned to Andrew and Tom 
12. Allow meta-data--github #23--it was decided that for v.1 any NineML element can contain an “annotation” sub-element. Any valid xml can be put in the annotation element; however, it is recommended to use a standard annotation xml language, such as rdf--assigned to Tom
13. Adding cell layouts to populations or projections--should be a module or sep. package. Can be v.1. if Ivan has done something on the is already, if not wait until v.2. Ask Tom whether there is an initial implementation. 
14. Add “type” attribute to component classes--this idea was rejected before by the TF.--see Github #6



B. Version 2 Requirements/Actions
1. Basic experimental setup specification
2. Adding support for SBML subset of MathML
3. Add "Constant" tag for numerical constants--need to discuss this one 
4. see GitHub #29 requirements for extensions to NineML (also see #3 in the Future meetings and the upkeep of NineML section
5. components to define computed properties
6. specifying dimensions (as in LEMS)
7. using “UncertML” elements to define random distribution (github #31)


1. extensible parameters for connection lists
2. Do we need a separate “AnalogOut” element to match “EventOut” instead of just using Alias/StateVariable’? (syntax)
3. specification of subsets
4. global properties
5. allow events to have a scalar
6. adding support for SBML and MathML
7. Basically experimental setup specification--see github#22--Alex will put forth a proposal and lead discussion on this.--assigned to Alex
8. Add subcomponents to dynamic classes--see github#4 for proposal--subcomponent containers “ComponentGroup” should be part of the user layer. Also includes a syntax to expose ports external to the component container.
9. Partial specification of component classes-see github #40 for an example of  what the parameterization of component groups could look like. instead of partially specified component, the problem will be addressed by altered copies of existing parameterization--example provided in the tag.
10. splitting user layer into composition and parameterization layers--github#41--the term user is somewhat loaded so would like to split it into 2 parts: composition layer--in which all ports and component classes are connected and parameterization layer--holds the parameters of the model. also should consider the state layer--github#36
11. adding cell layouts to populations or projections--github#19
12. Handling more complex scenarios for XML syntax for projections--github #33.
13. Extensions for canonical layouts (syntactic sugar) like NEURON's kinetics syntax
14. Components to define computed properties (eg distant dependent weights)



C. Discussion points deferred to future releases
1. Proposal for multi-compartmental models
2. Array ports to enable components to pass a variable number of parameters between each other
3. Valid parameter ranges?
Future meetings and the upkeep of NineML
1. Procedure for proposed changes to the specification
   1. Proposed changes should be discussed via the GitHub issue tracker and “+1” by at least 2 other members from different institutions.
   2. Any changes to the specification need to be made via a pull request to the relevant branch (see point 1c). To be accepted as part of the standard all active members of the committee must comment and we will try to achieve consensus but in the event that consensus cannot be achieved ⅔ of the active members must agree with the PR (cf NineML bylaws).
   3. Bug-fixes are made to the INCF/master branch with tags for each minor version increment. Enhancements destined for the next release (see 1b) are made to the INCF/dev branch. 
   4. Once a consensus has been achieved that the enhancements in the dev branch warrant a new major release, a face-to-face meeting will be organised to review the specification and approve the release (either in person or online).
   5. Once a new major release has been approved the master branch will be renamed after the former version number (eg. version2) and the dev branch will be merged into the master branch.
1. Future Meetings
   1. Meeting formats
      1. Online teleconferences
      2. In-person meetings (plan for 2 in-person meetings in 2015--possible dates: end of March (open location), end of May, beginning of June--in Sheffield)
   1. Meeting schedules
      1. Regular in-person meetings 1-2 times per year
      2. Online teleconferences as required
1. Requirements for “Extensions” to NineML
   1. The ‘Core’ of NineML is defined in the Specification, excepting those parts specifically described as Extensions.
   2. Extensions provide high level descriptive power to NineML
   3. Extensions MUST be collapsible to Core descriptions, and provide two way conversion (in the form of standalone tools) between the Extension level description and the Core description (Extension information can be stored in annotations)
   4. To support 3c, all tools must pass through annotations relating to Extensions (all annotations should be passed through anyway).
   5. The rationale behind these requirements is to minimise the amount of updating that tool builders and code generation builders need to do (as long as the core is supported all extensions should also be supported via collapsing to the core).
