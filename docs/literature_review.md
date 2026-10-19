# Literature review: grid stress, climate heat and cascading impacts on critical services

## 1. Introduction
Power systems underpin almost every other kind of infrastructure, so how well they hold up under hazards and a warming climate matters well beyond the electricity sector. Three bodies of research bear on this, and they have mostly grown up separately:
- **Power-system engineering** models physical network behaviour in detail but usually stops at the substation boundary.
- **Infrastructure-interdependency research** captures how failures spread between sectors but often simplifies the electrical physics.
- **Climate-impact studies** quantify changes in temperature and demand but seldom carry them through to contingency performance.

This review covers contingency analysis, hazard-driven resilience, distribution networks with distributed solar, climate-driven thermal derating, interdependent infrastructure, and backup power for critical facilities. It ends by identifying the gap this project addresses.

## 2. Security assessment and contingency analysis
Steady-state security goes back to Alsac & Stott (1974), who built security constraints into optimal load flow using the IEEE 30-bus system. Stott, Alsac & Monticelli (1987) set out the framework still used today: a system is secure if it withstands any single credible contingency without thermal overloads, voltage violations or instability (the N-1 criterion). Wood, Wollenberg & Sheblé (2013) give the textbook treatment of the process. In India, the CEA *Manual on Transmission Planning Criteria* (2013, revised 2023) writes N-1 and N-1-1 into planning practice.

Simulating every contingency is computationally heavy. Ejebe & Wollenberg (1979) therefore proposed performance indices that rank outages by severity, the direct ancestor of "critical lines" lists.

Natural hazards break the N-1 assumption of independent, one-at-a-time outages, because they remove several nearby assets at once. Salmeron, Wood & Baldick (2004) framed the N-k problem as bilevel interdiction, with load shed as the damage metric. Bienstock & Verma (2010) developed scalable formulations. Estimating load shed needs either an OPF with sheddable loads (Frank et al., 2012) or a heuristic rule.

Most N-k studies search for adversarial worst cases. Fewer use physically motivated hazard footprints such as a storm corridor, which is the approach taken here. The Indian grid disturbances of July 2012 (Ministry of Power, 2012) show in practice the cascading failure that contingency analysis is meant to anticipate.

## 3. Hazard-driven outages and resilience
Attention has widened from reliability (frequent, low-impact events) to resilience (rare, high-impact events). Panteli & Mancarella (2015) proposed the "resilience trapezoid": disturbance, degraded operation and restoration phases, with infrastructure resilience separated from operational resilience. Wang et al. (2016) called for hazard-specific models that link the hazard to network impact.

Panteli et al. (2017) combined wind fragility curves with sequential Monte Carlo simulation to estimate load shed and compare adaptation measures. Espinoza et al. (2016) and Ouyang & Dueñas-Osorio (2014) stressed that resilience has several dimensions, covering resistance, absorption and recovery.

Two lessons shape this project. First, the spatial footprint of a hazard, not random independent failures, should define multi-element contingencies. Second, outage *duration* matters as much as extent. The Cyclone Fani assessment (Government of Odisha et al., 2019) documents restoration periods of days to weeks in India.

## 4. Distribution networks and distributed solar
Most customer interruptions start on distribution networks, and these networks are being reshaped by rooftop PV. Walling et al. (2008) summarise the effects of distributed generation: voltage rise, reverse power flow, protection problems and thermal loading. Voltage rise is usually the first limit reached. Tonkoski et al. (2011) proposed coordinated curtailment to prevent it.

These limits are usually expressed as hosting capacity, which Ismael et al. (2019) review. Voltage limits come from IEEE 1547-2018 and the CEA connectivity regulations. The CIGRE benchmark systems (Strunz et al., 2014) are the reference test feeders for this kind of study.

Distributed PV has a double role: it can cause voltage violations in normal operation, and it can supply local load during an outage. These two views are rarely combined, and this project links them (3B → 3E).

## 5. Climate change, heat and conductor ratings
Overhead-line ampacity is set by a heat balance: joule and solar heating on one side, convective and radiative cooling on the other. IEEE Std 738 and CIGRE TB 601 (2014) both formulate it. Arroyo et al. (2015) validated both against measurements on a 132 kV line and found wind to be the most uncertain input. Douglass et al. (2019) review dynamic line rating, which uses the same physics.

Bartos et al. (2016) applied downscaled temperature projections to IEEE 738 ratings across the US. They found lower summer capacity combined with higher peak load, a "double squeeze" on grid margins. Sathaye et al. (2013) reached similar conclusions for California, and Craig et al. (2018) noted that most operational studies still ignore derating.

For India, Rohini et al. (2016) document rising heatwave trends and Mishra et al. (2017) project sharply higher heat exposure. Yet applying conductor heat balance to Indian projections, and counting the contingencies that become violations under derated ratings, is largely absent from the literature.

## 6. Climate projection data
CMIP6 (Eyring et al., 2016) and ScenarioMIP (O'Neill et al., 2016) define the SSP scenarios. NEX-GDDP-CMIP6 (Thrasher et al., 2022) provides bias-corrected daily maximum temperature, wind and shortwave radiation at about 25 km resolution: the three main IEEE 738 inputs. Google Earth Engine (Gorelick et al., 2017) hosts it. Mishra, Bhatia & Tiwari (2020) offer an independent South Asian CMIP6 product for cross-checks. Downscaled wind is less reliable than temperature, so its uncertainty should be shown explicitly.

## 7. Interdependent infrastructure and cascading impacts
Rinaldi, Peerenboom & Kelly (2001) classify interdependencies as physical, cyber, geographic and logical. Ouyang (2014) reviews the modelling approaches and singles out network-based models for their clarity and scalability. Haimes & Jiang (2001) offer a sector-level economic alternative.

Buldyrev et al. (2010) showed that coupled networks can collapse abruptly. Hines et al. (2010), however, caution that topology alone misjudges how vulnerable a power grid is. Together these findings support a hybrid design: power-flow physics decides which buses lose supply, and a dependency graph carries those losses to the services that depend on them.

Thacker, Pant & Hall (2017) and Pant et al. (2018) traced disruption from failed assets to the customers who lose service, and found that indirect effects through dependencies can exceed direct exposure. Their "people disrupted × duration" metric is the precursor of the critical service-hours metric used here. On the health side, Klinger et al. (2014) and Casey et al. (2020) document how outages harm health through equipment failure, cold chain, water and heat. The power → water → hospital chain is often described but rarely modelled within a grid contingency framework.

## 8. Backup power for critical facilities
Anderson et al. (2018) measure how long PV-battery systems can sustain critical loads through outages and put a value on that resilience. Laws et al. (2018) show that valuing resilience changes the cost-optimal size, usually favouring larger batteries. Both build on REopt (Cutler et al., 2017), and Khatib et al. (2016) review sizing methods.

For the Global South, Franco et al. (2017) and WHO / World Bank / SEforALL / IRENA (2023) document energy needs of healthcare facilities. CEEW (2020) reports Indian evidence from solarised health centres in Chhattisgarh.

Most sizing studies assume an arbitrary outage duration such as 24 or 72 hours. Few derive it from grid contingency and hazard analysis.

## 9. Research gap
1. Climate derating is rarely carried through to contingency performance, and almost never for Indian climate conditions.
2. Hazard footprints are rarely linked to service-level outcomes such as critical service-hours (Sendai Target D).
3. Distributed PV is treated as either a problem (hosting capacity) or a solution (backup), seldom both on the same feeder.
4. Mitigation is sized against assumed outage durations rather than modelled ones.

This project addresses these gaps with one reproducible open workflow, from hazard and heat, through grid contingencies and dependent-service disruption, to cost-assessed mitigation.

## References
- Alsac, O., Stott, B. (1974). Optimal load flow with steady-state security. *IEEE Trans. PAS*, 93(3), 745–751.
- Anderson, K. et al. (2018). Quantifying and monetizing renewable energy resiliency. *Sustainability*, 10(4), 933.
- Arroyo, A. et al. (2015). Comparison between IEEE and CIGRE thermal behaviour standards and measured temperature on a 132-kV overhead power line. *Energies*, 8(12), 13660–13671.
- Bartos, M. et al. (2016). Impacts of rising air temperatures on electric transmission ampacity and peak electricity load in the United States. *Environ. Res. Lett.*, 11, 114008.
- Bienstock, D., Verma, A. (2010). The N−k problem in power grids. *SIAM J. Optim.*, 20(5), 2352–2380.
- Buldyrev, S. et al. (2010). Catastrophic cascade of failures in interdependent networks. *Nature*, 464, 1025–1028.
- Casey, J. et al. (2020). Power outages and community health: a narrative review. *Curr. Environ. Health Rep.*, 7, 371–383.
- CEA (2013, rev. 2023). *Manual on Transmission Planning Criteria*. Central Electricity Authority, India.
- CEEW (2020). *Powering Primary Healthcare through Solar in India: Lessons from Chhattisgarh*.
- CIGRE TB 601 (2014). *Guide for Thermal Rating Calculations of Overhead Lines*.
- Craig, M. et al. (2018). A review of the potential impacts of climate change on bulk power system planning and operations in the United States. *Renew. Sustain. Energy Rev.*, 98, 255–267.
- Cutler, D. et al. (2017). *REopt: A Platform for Energy System Integration and Optimization*. NREL/TP-7A40-70022.
- Douglass, D. et al. (2019). A review of dynamic thermal line rating methods with forecasting. *IEEE Trans. Power Deliv.*, 34(6), 2100–2109.
- Ejebe, G., Wollenberg, B. (1979). Automatic contingency selection. *IEEE Trans. PAS*, 98(1), 97–109.
- Espinoza, S. et al. (2016). Multi-phase assessment and adaptation of power systems resilience to natural hazards. *Electr. Power Syst. Res.*, 136, 352–361.
- Eyring, V. et al. (2016). Overview of the CMIP6 experimental design and organization. *Geosci. Model Dev.*, 9, 1937–1958.
- Franco, A. et al. (2017). A review of sustainable energy access and technologies for healthcare facilities in the Global South. *Sustain. Energy Technol. Assess.*, 22, 92–105.
- Frank, S. et al. (2012). Optimal power flow: a bibliographic survey I. *Energy Systems*, 3, 221–258.
- Gorelick, N. et al. (2017). Google Earth Engine: planetary-scale geospatial analysis for everyone. *Remote Sens. Environ.*, 202, 18–27.
- Government of Odisha, World Bank, ADB, UN (2019). *Cyclone Fani: Damage, Loss and Needs Assessment*.
- Haimes, Y., Jiang, P. (2001). Leontief-based model of risk in complex interconnected infrastructures. *J. Infrastruct. Syst.*, 7(1), 1–12.
- Hines, P. et al. (2010). Do topological models provide good information about electricity infrastructure vulnerability? *Chaos*, 20(3), 033122.
- Holmgren, W. et al. (2018). pvlib python: a python package for modeling solar energy systems. *J. Open Source Softw.*, 3(29), 884.
- IEEE Std 738-2012. *Standard for Calculating the Current-Temperature Relationship of Bare Overhead Conductors*.
- IEEE Std 1547-2018. *Interconnection and Interoperability of Distributed Energy Resources*.
- Ismael, S. et al. (2019). State-of-the-art of hosting capacity in modern power systems with distributed generation. *Renew. Energy*, 130, 1002–1020.
- Khatib, T. et al. (2016). A review on sizing methodologies of photovoltaic array and storage battery in a standalone photovoltaic system. *Energy Convers. Manag.*, 120, 430–448.
- Klinger, C. et al. (2014). Power outages, extreme events and health: a systematic review. *PLOS Currents Disasters*.
- Laws, N. et al. (2018). Impacts of valuing resilience on cost-optimal PV and storage systems for commercial buildings. *Renew. Energy*, 127, 896–909.
- Ministry of Power (2012). *Report of the Enquiry Committee on Grid Disturbance in Northern Region on 30 July 2012 and in Northern, Eastern & North-Eastern Region on 31 July 2012*.
- Mishra, V. et al. (2017). Heat wave exposure in India in current, 1.5 °C, and 2.0 °C worlds. *Environ. Res. Lett.*, 12, 124012.
- Mishra, V., Bhatia, U., Tiwari, A. (2020). Bias-corrected climate projections for South Asia from CMIP6. *Sci. Data*, 7, 338.
- O'Neill, B. et al. (2016). The Scenario Model Intercomparison Project (ScenarioMIP) for CMIP6. *Geosci. Model Dev.*, 9, 3461–3482.
- Ouyang, M. (2014). Review on modeling and simulation of interdependent critical infrastructure systems. *Reliab. Eng. Syst. Saf.*, 121, 43–60.
- Ouyang, M., Dueñas-Osorio, L. (2014). Multi-dimensional hurricane resilience assessment of electric power systems. *Struct. Saf.*, 48, 15–24.
- Pant, R. et al. (2018). Critical infrastructure impact assessment due to flood exposure. *J. Flood Risk Manag.*, 11(1), 22–33.
- Panteli, M., Mancarella, P. (2015). The grid: stronger, bigger, smarter? *IEEE Power Energy Mag.*, 13(3), 58–66.
- Panteli, M. et al. (2017). Power system resilience to extreme weather: fragility modeling, probabilistic impact assessment, and adaptation measures. *IEEE Trans. Power Syst.*, 32(5), 3747–3757.
- Rinaldi, S., Peerenboom, J., Kelly, T. (2001). Identifying, understanding, and analyzing critical infrastructure interdependencies. *IEEE Control Syst. Mag.*, 21(6), 11–25.
- Rohini, P., Rajeevan, M., Srivastava, A. (2016). On the variability and increasing trends of heat waves over India. *Sci. Rep.*, 6, 26153.
- Salmeron, J., Wood, K., Baldick, R. (2004). Analysis of electric grid security under terrorist threat. *IEEE Trans. Power Syst.*, 19(2), 905–912.
- Sathaye, J. et al. (2013). Estimating impacts of warming temperatures on California's electricity system. *Glob. Environ. Change*, 23(2), 499–511.
- Stott, B., Alsac, O., Monticelli, A. (1987). Security analysis and optimization. *Proc. IEEE*, 75(12), 1623–1644.
- Strunz, K. et al. (2014). *Benchmark Systems for Network Integration of Renewable and Distributed Energy Resources*. CIGRE TB 575.
- Thacker, S., Pant, R., Hall, J. (2017). System-of-systems formulation and disruption analysis for multi-scale critical national infrastructures. *Reliab. Eng. Syst. Saf.*, 167, 30–41.
- Thrasher, B. et al. (2022). NASA Global Daily Downscaled Projections, CMIP6. *Sci. Data*, 9, 262.
- Thurner, L. et al. (2018). pandapower — an open-source Python tool for convenient modeling, analysis, and optimization of electric power systems. *IEEE Trans. Power Syst.*, 33(6), 6510–6521.
- Tonkoski, R. et al. (2011). Coordinated active power curtailment of grid connected PV inverters for overvoltage prevention. *IEEE Trans. Sustain. Energy*, 2(2), 139–147.
- Walling, R. et al. (2008). Summary of distributed resources impact on power delivery systems. *IEEE Trans. Power Deliv.*, 23(3), 1636–1644.
- Wang, Y. et al. (2016). Research on resilience of power systems under natural disasters — a review. *IEEE Trans. Power Syst.*, 31(2), 1604–1613.
- WHO, World Bank, SEforALL, IRENA (2023). *Energizing Health: Accelerating Electricity Access in Health-Care Facilities*.
- Wood, A., Wollenberg, B., Sheblé, G. (2013). *Power Generation, Operation, and Control* (3rd ed.). Wiley.

*Verify volume and page details on Google Scholar or IEEE Xplore before formal citation.*
