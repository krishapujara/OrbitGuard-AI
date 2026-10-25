# References

Primary sources used for formats, propagator behaviour, and risk caveats:

1. Kelso, T. S. CelesTrak GP data formats and query interface. https://celestrak.org/NORAD/elements/gp.php  
2. Hoots, F. R., & Roehrich, R. L. *Spacetrack Report No. 3: Models for Propagation of NORAD Element Sets* (1980).  
3. Vallado, D. A., Crawford, P., Hujsak, R., & Kelso, T. S. Revisiting Spacetrack Report #3. AIAA/AAS (2006). python-sgp4 implements this family of SGP4/SDP4 code.  
4. Rhodes, B. python-sgp4 documentation (TEME output, error codes, example satellite 00005). https://pypi.org/project/sgp4/  
5. Vallado, D. A. *Fundamentals of Astrodynamics and Applications* — TEME vs GCRF/ITRF discussion.  
6. Alfano, S. methods for collision probability in the encounter plane (as cited in conjunction-assessment literature).  
7. NASA Conjunction Assessment Risk Analysis (CARA) public descriptions of covariance-based Pc.  
8. ESA Space Debris Office. Space debris environment overview. https://www.esa.int/Space_Safety/Space_Debris  

Secondary implementation notes:

- Streamlit for the local dashboard; Plotly 3D traces labelled as propagated TEME, not observations.
- scikit-learn logistic regression as an interpretable baseline; no neural network on a single TLE snapshot.
