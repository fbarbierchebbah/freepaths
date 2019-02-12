from numpy import pi, cos, sin, tan, exp, arctan, arcsin, sign, zeros, log, sqrt, arccos
import matplotlib.pyplot as plt
import numpy as np
from random import random, choice, randint
from scipy.constants import k, hbar
import os
import time
from Lattices import hole_positioning, pillar_positioning


# SIMULATION PARAMETERS
output_folder_name='pillars'                                                   # You must create this folder before you start the simulation
number_of_phonons=100      
number_of_phonons_in_a_group=100                                               # To reduce the memory load, phonons are simulated in small groups
number_of_timesteps=40000
number_of_nodes=400                                                             # Resolution of distribution plots
timestep=0.5e-12                                                                # [s] Duration of one timestep
T=300.0                                                                           # [K] Temperature of the system

# SYSTEM DIMENSIONS [m]
width=400e-9
length=400e-9#2275e-9
thickness=50e-9

# ROUGHNESS [m]
side_wall_roughness=1.0e-9
hole_roughness=2.0e-9
pillar_roughness=2.0e-9
top_roughness=0.2e-9
bottom_roughness=0.2e-9
pillar_top_roughness=2.0e-9

# SCATTER PARAMETERS [m]
holes='no'                                                             
hole_lattice_type='square'#'square'                                # Choose between 'square', 'serpentine', 'cloak', 'turn' etc
pillars='yes'
pillar_lattice_type='square'
circular_hole_diameter=50e-9#185e-9
rectangular_hole_side_x=150e-9#545e-9
rectangular_hole_side_y=200e-9#390e-9                                                        
pillar_height=30e-9
pillar_wall_angle=pi/3                                                          # DO NOT CHANGE
period_x=70e-9
period_y=70e-9

# ENERGY MAP PARAMETERS
number_of_pixels_x=40#int(0.2*width*1e9)
number_of_pixels_y=40#int(0.2*length*1e9)
number_of_timeframes=20

# MATERIAL PARAMETERS
specific_heat_capacity=700 #[J/kg/K]
material_density=2330 #[kg/m^3]

def initialization():
    '''This function initializes position and angles of a phonon'''
    if hole_lattice_type=='serpentine':
        x=-width/2+(155e-9)/2+0.4*(155e-9)*(2*random()-1)
    elif hole_lattice_type=='diode_with_wires':
        x=0.4*(period_x-rectangular_hole_side_x)*(2*random()-1)
    elif hole_lattice_type=='turn':
        x=0.4*(period_x*5)*(2*random()-1)
    else:
        x=0.4*width*(2*random()-1)                                              # Here 0.4 is to prevent initialization right next to a wall                                             
    y=1e-12
    z=0.4*thickness*(2*random()-1)
    #theta[:]=arcsin(2*random()-1)                                              # Lambert cosine distribution
    #phi[:]=arcsin(2*random()-1)   
    theta=-pi/2+pi*random()                                                     # Random distribution
    phi=-pi/2+pi*random()          
    return x, y, z, theta, phi


def bulk_phonon_dispersion(N):
    '''This function returns phonon dispersion calculated for N wavevectors over the G-X direction'''
    dispersion=zeros((N,4))                                                
    dispersion[:,0]=[k*12e9/(N-1) for k in range(N)]                                                                # Ref. APL 95 161901 (2009)
    dispersion[:,1]=[abs(1369.42*k-2.405e-8*(k**2)-9.70e-19*(k**3)) for k in dispersion[:,0]]                       # LA branch
    dispersion[:,2]=[abs(1081.74*k-7.711e-8*(k**2)+5.674e-19*(k**3)+7.967e-29*(k**4)) for k in dispersion[:,0]]     # TA branch
    dispersion[:,3]=dispersion[:,2]                                                                                 # TA branch 
    return dispersion   


def phonon_properties_assignment():
    '''This function assigns phonon frequency (f) according to the Plank distribution at a given temperature T,
    choses polarization and calculates group velocity from bulk disperion'''
    default_speed=6000                                                          # [m/s] This is the speed for Debye approximation
    f_max=default_speed/(2*pi*hbar*default_speed/(2.82*k*T))                    # Frequency of the peak of the Plank distribution
    DOS_max=3*((2*pi*f_max)**2)/(2*(pi**2)*(default_speed**3))                  # DOS for f_max in Debye approximation
    bose_einstein_max=1/(exp((hbar*2*pi*f_max)/(k*T))-1)                        # Bose-Einstein destribution for f_max
    plank_distribution_max=DOS_max*hbar*2*pi*f_max*bose_einstein_max            # Peak of the distribution (needed for normalization)
    i=0
    while i==0:                                                                 # Until we obtain the frequency
        f=f_max*5*random()                                                      # Let's draw a random frequency in the 0 - 5*f_max range
        DOS=3*((2*pi*f)**2)/(2*(pi**2)*(default_speed**3))                      # Calculate the DOS in Debye approximation
        bose_einstein=1/(exp((hbar*2*pi*f)/(k*T))-1)                            # And the Bose-Einstein destribution
        plank_distribution=DOS*hbar*2*pi*f*bose_einstein                        # Plank distribution            
        if random()<plank_distribution/plank_distribution_max and f<1.12e13:    # Deciding if this frequency belongs to the Plank distribution and dispersion
            break                                                               # We take normalized distribution and draw a random number to see if it is under the curve
    polarization=choice(['TA','TA','LA'])                                       # There are two TA branches and one LA branch    
    dispersion=bulk_phonon_dispersion(5000)
    
    if polarization=='TA' and f<4.5e12:                                         # Limit <4.5e12 because TA branches in Si end there
        j=(np.abs(dispersion[:,2] - f)).argmin()
        speed=2*pi*abs(dispersion[j+1,2]-dispersion[j,2])/abs(dispersion[j+1,0]-dispersion[j,0])
    else:                                                                       # i.e. LA polarization
        j=(np.abs(dispersion[:,1] - f)).argmin()
        speed=2*pi*abs(dispersion[j+1,1]-dispersion[j,1])/abs(dispersion[j+1,0]-dispersion[j,0])        
    #speed=3000
    phonon_properties = [f, polarization, speed]
    return phonon_properties


def phonon_properties_assignment_2(j, branch):
    '''This function assigns phonon frequency (f) according to the wavevector & branch and calculates group velocity from bulk disperion'''
    dispersion=bulk_phonon_dispersion(number_of_phonons+1)
    K=(dispersion[j+1,0]+dispersion[j,0])/2                                     # Wavevector (we take average in the interval)
    dK=(dispersion[j+1,0]-dispersion[j,0])                                      # Delta wavevector
    w=2*pi*abs((dispersion[j+1,branch+1]+dispersion[j,branch+1])/2)             # Angular freequency  (we take average in the interval)
    dw=2*pi*abs(dispersion[j+1,branch+1]-dispersion[j,branch+1])                # Delta angular freequency        
    speed=dw/dK                                                                 # Group velocity
    frequency=w/(2*pi)
    polarization='LA'*(branch == 0)*1+'TA'*(branch != 0)*1                      # Polarization according to the branch                                        
    phonon_properties = [frequency, polarization, speed]
    return phonon_properties, w, K, dK


def move(x, y, z, theta, phi, speed):
    '''This function moves a phonon in one timestep and returns new coordinates'''
    x+=sin(theta)*abs(cos(phi))*speed*timestep
    y+=cos(theta)*abs(cos(phi))*speed*timestep
    z+=sin(phi)*speed*timestep
    return x, y, z


def scattering_on_rectangular_holes(x, y, z, theta, phi, f, speed, x0, y0, Lx, Ly):
    '''This function checks if the phonon strikes a rectangular hole and what is the new direction after the scattering'''
    x,y,z=move(x,y,z,theta,phi,speed)                                           # We make a test step to check if the scattering occurs on the next step
    if abs(x-x0)<=Lx/2 and abs(y-y0)<=Ly/2:                                     # If the phonon is inside the rectangle
        y1=(y0-y)+cos(theta)*(Lx/2-abs(x0-x))/abs(sin(theta))                   # y coordinate of the intersection with the hole side
        if abs(y1)<=Ly/2:                                                       # Sidewalls scattering 
            a=arccos(cos(phi)*sin(abs(theta)))                                  # Angle to the normale to the surface
            p=exp(-16*(pi**2)*(hole_roughness**2)*((cos(a))**2)/((speed/f)**2)) # Specular scattering probability    
            if random()<p:                                                      # Specular scattering
                new_theta=-theta
                new_phi=phi
                scattering_type='specular'    
            else:                                                               # Diffuse scattering                                                       
                new_theta=-sign(sin(theta))*pi/2+arcsin(2*random()-1)           # Lambert cosine distribution
                new_phi=arcsin(2*random()-1)
                scattering_type='diffuse'
        else:                                                                   # Top and bottom scattering
            a=arccos(cos(phi)*cos(theta))                                       # Angle to the surface
            p=exp(-16*(pi**2)*(hole_roughness**2)*((cos(a))**2)/((speed/f)**2)) # Specular scattering probability
            if random()<p:                                                      # Specular scattering
                new_theta=sign(theta)*pi-theta
                new_phi=phi
                scattering_type='specular'
            else:
                if abs(theta)>=pi/2:                                            # Top surface
                    new_theta=arcsin(2*random()-1)                              # Lambert cosine distribution
                else:                                                           # Bottom surface
                    rand_sign=sign((2*random()-1))
                    new_theta=rand_sign*pi-rand_sign*arcsin(random())           # Lambert cosine distribution
                new_phi=arcsin(2*random()-1)
                scattering_type='diffuse'                              
    else:
        new_theta=theta
        new_phi=phi
        scattering_type='no_scattering'
    return new_theta, new_phi, scattering_type


def scattering_on_circular_holes(x,y,z,theta,phi,f,speed,x0,y0,R):
    '''This function checks if a phonon strikes a circular hole and what is the new direction after the scattering'''
    x,y,z=move(x,y,z,theta,phi,speed)                                           # We make a test step to check if the scattering occurs on the next step
    if (x-x0)**2+(y-y0)**2 <= R**2:                                             # If the phonon is inside the circle with radius R        
        tangent_theta=arctan((x-x0)/(y-y0))                                           
        a=arccos(cos(phi)*cos(theta+sign(y-y0)*tangent_theta))                  # Angle to the surface (note that equation depends on the top/bottom side)
        p=exp(-16*(pi**2)*(hole_roughness**2)*((cos(a))**2)/((speed/f)**2))      # Specular scatteing probability
        if random()<p:                                                          # Specular scattering
            new_theta=-theta-pi+2*tangent_theta
            new_phi=phi
            scattering_type='specular'                      
        else:                                                                   # Diffuse scattering
            if y>=y0:                                                           # Scattering on the top surface of a hole
                new_theta=tangent_theta-arcsin(2*random()-1)
            else:                                                               # Scattering on the bottom surface of a hole
                new_theta=-pi+tangent_theta-arcsin(2*random()-1)
            new_phi=arcsin(2*random()-1)
            scattering_type='diffuse'
    else:
        new_theta=theta
        new_phi=phi
        scattering_type='no_scattering'
    return new_theta, new_phi, scattering_type


def scattering_on_circular_pillars(x,y,z,theta,phi,frequency,speed,x0,y0,R):
    '''This function checks if a phonon strikes a circular pillar and what is the new direction after the scattering'''
    x_previous=x
    y_previous=y
    x,y,z=move(x,y,z,theta,phi,speed)
    R=(circular_hole_diameter/2)-(z-thickness/2)/tan(pillar_wall_angle)         # Cone radius at a given z coordinate
    phi = phi-sign(phi)*pi*(abs(phi) > pi/2)
    if (x-x0)**2+(y-y0)**2 >= R**2 and (x-x0)**2+(y-y0)**2 < (R+2*speed*timestep)**2 and z > thickness/2: # i.e. if it at the boundary inside the pillar                                 
        tangent_theta=arctan((x-x0)/(y-y0))
        lam=speed/frequency                                                 
        a=arctan(tan((pi/2-theta)+tangent_theta)*cos(phi-(pi/2-pillar_wall_angle))) # Angle to the surface (Check if it's correctly corrected with pillar angle)
        p=exp(-16*(pi**2)*(pillar_roughness**2)*((cos(pi/2-a))**2)/(lam**2))      # Specular scatteing probability
        #p=1.0
        if random()<p:                                                          # Specular scattering            
            if sqrt((x-x0)**2+(y-y0)**2) >= sqrt((x_previous-x0)**2+(y_previous-y0)**2) :   # if phonon moves from the center of the pillar to the wall 
                if (phi < pi/2-2*pillar_wall_angle):                             # If theta does not reflect back
                    #new_phi=phi+2*pillar_wall_angle
                    new_phi=phi-(pi/2-pillar_wall_angle)                        # Pillar wall inclination is taken into account
                    new_theta=theta
                    #print "1"
                else:                                                           # Regular reflection
                    #new_phi=phi+2*pillar_wall_angle
                    new_theta=-theta-pi+2*tangent_theta
                    new_phi=phi-(pi/2-pillar_wall_angle)
                    #print "2"
            else:                                                               # Otherwise, if phonon strikes the wall as it goes towards the center
                new_phi=-sign(phi)*phi-2*pillar_wall_angle
                new_theta=theta
                #print "3"
                 
            scattering_type='specular'                      
        else:                                                                   # Diffuse scattering
            if y>=y0:                                                           # Scattering on the top surface of a hole
                new_theta=tangent_theta+pi-arcsin(2*random()-1)
            else:                                                               # Scattering on the bottom surface of a hole
                new_theta=tangent_theta-arcsin(2*random()-1)
            new_phi=arcsin(2*random()-1)-(pi/2-pillar_wall_angle)               # Pillar wall inclination is taken into account
            scattering_type='diffuse'
    else:
        new_theta=theta
        new_phi=phi
        scattering_type='no_scattering'
    return new_theta, new_phi, scattering_type


def scattering_on_triangle_down_holes(x, y, z, theta, phi, f, speed, x0, y0, Lx, Ly, all_scat_stat):
    '''This function checks if the phonon strikes a reverse triangular hole and what is the new direction after the scattering'''
    x,y,z=move(x,y,z,theta,phi,speed)                                           # We make a step to check if the scattering occurs on the next step
    beta=arctan(0.5*Lx/Ly)                                                      # Angle of the triangle (tip angle)
    if Ly/2-(y-y0)<=(Lx/2-abs(x-x0))/tan(beta) and abs(y-y0)<Ly/2:
        if (y+timestep*speed > y0+Ly/2) and (abs(theta)>pi/2):                  # Top side scattering
            a=arccos(cos(phi)*cos(theta))                                       # Angle to the surface
            p=exp(-16*(pi**2)*(hole_roughness**2)*((cos(a))**2)/((speed/f)**2)) # Specular scattering probability
            if random()<p:                                                      # Specular scattering
                new_theta=sign(theta)*pi-theta
                new_phi=phi
                scattering_type='specular'
            else:                                                               # Diffuse scattering
                new_theta=arcsin(2*random()-1)                                  # Lambert cosine distribution
                new_phi=arcsin(2*random()-1)
                scattering_type='diffuse'
        else:                                                                   # Sidewalls scattering 
            a=arccos(cos(phi)*cos(theta-sign(x-x0)*(pi/2-beta)))                # Angle to the surface
            p=exp(-16*(pi**2)*(hole_roughness**2)*((cos(a))**2)/((speed/f)**2)) # Specular scattering probability
            if random()<p:                                                      # Specular scattering
                new_theta=-theta+sign(x-x0)*2*beta
                new_phi=phi
                scattering_type='specular'  
                if x>x0:
                    all_scat_stat.append(new_theta)                                       
            else:                                                               # Diffuse scattering                                                       
                rand_sign=sign((2*random()-1))
                new_theta=rand_sign*pi-rand_sign*arcsin(random())-sign(x-x0)*(pi/2-beta)  # Lambert cosine distribution
                new_phi=arcsin(2*random()-1)
                scattering_type='diffuse'
    else:
        new_theta=theta
        new_phi=phi
        scattering_type='no_scattering'
    return new_theta, new_phi, scattering_type, all_scat_stat


def scattering_on_triangle_up_holes(x, y, z, theta, phi, f, speed, x0, y0, Lx, Ly, all_scat_stat):
    '''This function checks if the phonon strikes a reverse triangular hole and what is the new direction after the scattering'''
    x,y,z=move(x,y,z,theta,phi,speed)                                           # We make a step to check if the scattering occurs on the next step
    beta=arctan(0.5*Lx/Ly)                                                      # Angle of the triangle (tip angle)
    if Ly/2+(y-y0)<=(Lx/2-abs(x-x0))/tan(beta) and abs(y-y0)<Ly/2:
        #x1=Ly/2/tan(theta) - abs(y0-y)/tan(theta) + abs(x0-x)
        if ((y-timestep*speed) < (y0-Ly/2)) and (abs(theta)<pi/2):                  # Bottom scattering
            a=arccos(cos(phi)*cos(theta))                                       # Angle to the surface
            p=exp(-16*(pi**2)*(hole_roughness**2)*((cos(a))**2)/((speed/f)**2)) # Specular scattering probability
            if random()<p:                                                      # Specular scattering
                new_theta=sign(theta)*pi-theta
                new_phi=phi
                scattering_type='specular'
            else:                                                               # Diffuse scattering
                rand_sign=sign((2*random()-1))
                new_theta=rand_sign*pi-rand_sign*arcsin(random())               # Lambert cosine distribution
                new_phi=arcsin(2*random()-1)
                scattering_type='diffuse'
        else:                                                                   # Sidewalls scattering 
            a=arccos(cos(phi)*cos(theta+sign(x-x0)*(pi/2-beta)))                # Angle to the surface
            p=exp(-16*(pi**2)*(hole_roughness**2)*((cos(a))**2)/((speed/f)**2)) # Specular scattering probability
            if random()<p:                                                      # Specular scattering
                new_theta=-theta-sign(x-x0)*2*beta
                new_phi=phi
                scattering_type='specular'
                if x>x0:
                    all_scat_stat.append(new_theta)                                       
            else:                                                               # Diffuse scattering                                                       
                new_theta=arcsin(2*random()-1)+sign(x-x0)*(pi/2-beta)           # Lambert cosine distribution
                new_phi=arcsin(2*random()-1)
                scattering_type='diffuse' 
    else:
        new_theta=theta
        new_phi=phi
        scattering_type='no_scattering'
    return new_theta, new_phi, scattering_type, all_scat_stat


def internal_scattering_time_calculation(frequency, polarization):
    '''This function determines time after which this phonon will undegro internal scattering'''
    w=2*pi*frequency
    deb_temp=152                                                                # [K] Debay temperature
    tau_impurity=1/((2.95e-45)*(w**4))
    tau_umklapp=1/((0.95e-19)*(w**2)*T*exp(-deb_temp/T))
    #if polarization=='TA':
    #    tau_umklapp=4/((3.28e-19)*(w**2)*T*exp(-140/T))                        # Ref. JAP 110, 034308 (2011)
    #if polarization=='LA':
    #    tau_umklapp=1/((3.28e-19)*(w**2)*T*exp(-140/T))    
    #if polarization=='TA':
    #    tau_norm=1/(9.3e-13*w*(T**4))
    #if polarization=='LA':
    #    tau_norm=1/((2.0e-24)*(w**2)*(T**3))
    #tau_total=1/((1/tau_impurity)+(1/tau_norm)+(1/tau_umklapp)) 
    tau_internal=1/((1/tau_impurity)+(1/tau_umklapp))
    time_of_internal_scattering=-log(random())*tau_internal                     # Ref. PRB 94, 174303 (2016)
    return time_of_internal_scattering


def internal_scattering(theta, phi, time_since_previous_scattering, time_of_internal_scattering):
    '''This function is checking is the time passed since previous diffuse scattering event 
    reached the time until an internal scatteringevent, and if yes, scatters randomly'''
    internal_scattering_type='none'    
    if time_since_previous_scattering > time_of_internal_scattering:
        theta=-pi+random()*2*pi
        phi=-pi+random()*2*pi
        internal_scattering_type='diffuse'
    return theta, phi, internal_scattering_type


def side_wall_scattering(x, y, z, theta, phi, frequency, speed):
    '''This fuction checks if the phonon hits a side wall and outputs new vector'''
    x,y,z=move(x,y,z,theta,phi,speed)
    scattering_type='no_scattering'
    if abs(x) > width/2 :                                                       # Check if we hit the wall
        lam=speed/frequency                                                     
        a=arccos(cos(phi)*sin(abs(theta)))                                      # Angle to the surface
        p=exp(-16*(pi**2)*(side_wall_roughness**2)*((cos(a))**2)/(lam**2)) # Specular scatteing probability  
        if random()<p:                                                          # Specular scattering
            theta=-theta
            scattering_type='specular'                                          # Each time we record scattering type
        else:                                                                   # Diffuse scattering                                                       
            theta=-sign(sin(theta))*pi/2+arcsin(2*random()-1)                   # Lambert cosine distribution
            #theta=-sign(sin(theta))*pi/2+0.5*pi*(2*random()-1)                 # Random distribution
            phi=arcsin(2*random()-1)
            scattering_type='diffuse'
    return theta, phi, scattering_type


def top_scattering(x, y, z, theta, phi, frequency, speed):
    '''This fuction checks if the phonon hits the top surface and outputs new vector'''
    x,y,z=move(x,y,z,theta,phi,speed) 
    scattering_type='no_scattering'
    if z > thickness/2:                                                         # Check if we hit the top surface 
        lam=speed/frequency                                                     
        p=exp(-16*(pi**2)*(top_roughness**2)*((cos(pi/2-phi))**2)/(lam**2))     # Specular scatteing probability
        if random()<p:                                                          # Specular scattering
            phi=-phi
            scattering_type='specular'                                          
        else:                                                                   # Diffuse scattering                                                       
            phi=-sign(sin(phi))*pi/2+arcsin(2*random()-1)                       # Lambert cosine distribution
            #new_phi=-sign(sin(phi))*pi/2+0.5*pi*(2*random()-1)                 # Random distribution
            theta=-pi+random()*2*pi
            scattering_type='diffuse'
    return theta, phi, scattering_type


def top_scattering_with_pillars(x, y, z, theta, phi, frequency, speed, pillar_coordinates):
    '''This fuction checks if the phonon hits the top surface and if this place has a pillar and outputs new vector'''
    x,y,z=move(x,y,z,theta,phi,speed) 
    scattering_type='no_scattering'
    if z > thickness/2:                                                         # Check if we hit the top surface 
        distances_from_centers=[0]*pillar_coordinates.shape[0]
        for i in range(pillar_coordinates.shape[0]):                            # For each pillar
            x0=pillar_coordinates[i,0]                                          # Coordinates of the pilla center
            y0=pillar_coordinates[i,1] 
            distances_from_centers[i]=(x-x0)**2+(y-y0)**2              
        if all((i > (circular_hole_diameter/2)**2) for i in distances_from_centers): # if it is not  under the pillar 
            lam=speed/frequency                                                     
            p=exp(-16*(pi**2)*(top_roughness**2)*((cos(pi/2-phi))**2)/(lam**2)) # Specular scatteing probability
            if random()<p:                                                      # Specular scattering
                phi=-phi
                scattering_type='specular'                                          
            else:                                                               # Diffuse scattering                                                       
                phi=-sign(sin(phi))*pi/2+arcsin(2*random()-1)                   # Lambert cosine distribution
                #new_phi=-sign(sin(phi))*pi/2+0.5*pi*(2*random()-1)             # Random distribution
                theta=-pi+random()*2*pi
                scattering_type='diffuse'
        elif z > pillar_height+thickness/2 and any((i > (circular_hole_diameter/2)**2) for i in distances_from_centers): # If it is the pillar top
            lam=speed/frequency                                                     
            p=exp(-16*(pi**2)*(pillar_top_roughness**2)*((cos(pi/2-phi))**2)/(lam**2))     # Specular scatteing probability
            if random()<p:                                                      # Specular scattering
                phi=-phi
                scattering_type='specular'                                          
            else:                                                               # Diffuse scattering                                                       
                phi=-sign(sin(phi))*pi/2+arcsin(2*random()-1)                   # Lambert cosine distribution
                #new_phi=-sign(sin(phi))*pi/2+0.5*pi*(2*random()-1)             # Random distribution
                theta=-pi+random()*2*pi
                scattering_type='diffuse'                    
    return theta, phi, scattering_type


def bottom_scattering(x, y, z, theta,phi, frequency, speed):    
    '''This fuction checks if the phonon hits the bottom surface and outputs new vector'''
    x,y,z=move(x,y,z,theta,phi,speed) 
    scattering_type='no_scattering'        
    if z < -thickness/2:                                                        # Check if we hit the bottom
        lam=speed/frequency                                                     
        p=exp(-16*(pi**2)*(bottom_roughness**2)*((cos(pi/2-phi))**2)/(lam**2))  # Specular scatteing probability
        if random()<p:                                                          # Specular scattering
            phi=-phi
            scattering_type='specular'                                          
        else:                                                                   # Diffuse scattering                                                       
            phi=-sign(sin(phi))*pi/2+arcsin(2*random()-1)                       # Lambert cosine distribution
            #phi=-sign(sin(phi))*pi/2+0.5*pi*(2*random()-1)                     # Random distribution
            theta=-pi+random()*2*pi
            scattering_type='diffuse'
    return theta, phi, scattering_type


def surface_scattering(x, y, z, theta, phi, frequency, hole_coordinates, hole_shapes, pillar_coordinates, speed, all_scat_stat):
    '''This function checks if there will be a surface scattering on this timestep and returns a new vector'''       
    hole_scattering_type = 'no_scattering'                                      # first, we assume there is no scattering
    pillar_scattering_type = 'no_scattering'
    if holes == 'yes':                                                          # If there are holes
        for i in range(hole_coordinates.shape[0]):                              # For each hole
            x0=hole_coordinates[i,0]                                            # Coordinates of the hole center
            y0=hole_coordinates[i,1]  
            if hole_shapes[i]=='circle':
                R=circular_hole_diameter*(1+hole_coordinates[i,2])/2            # Radius of the given hole
                theta,phi,hole_scattering_type=scattering_on_circular_holes(x,y,z,theta,phi,frequency,speed,x0,y0,R) #Scattering on this hole
            elif hole_shapes[i]=='rectangle':
                Lx=rectangular_hole_side_x*(hole_coordinates[i,2]+1)            # Correction of the hole size if there are holes of non standard size
                Ly=rectangular_hole_side_y*(hole_coordinates[i,2]+1)
                theta,phi,hole_scattering_type=scattering_on_rectangular_holes(x,y,z,theta,phi,frequency,speed,x0,y0,Lx,Ly)  #Scattering on this hole
            elif hole_shapes[i]=='triangle_down':
                Lx=rectangular_hole_side_x*(hole_coordinates[i,2]+1)            # Correction of the hole size if there are holes of non standard size
                Ly=rectangular_hole_side_y*(hole_coordinates[i,2]+1)
                theta,phi,hole_scattering_type,all_scat_stat=scattering_on_triangle_down_holes(x,y,z,theta,phi,frequency,speed,x0,y0,Lx,Ly,all_scat_stat)  #Scattering on this hole
            elif hole_shapes[i]=='triangle_up':
                Lx=rectangular_hole_side_x*(hole_coordinates[i,2]+1)            # Correction of the hole size if there are holes of non standard size
                Ly=rectangular_hole_side_y*(hole_coordinates[i,2]+1)
                theta,phi,hole_scattering_type,all_scat_stat=scattering_on_triangle_up_holes(x,y,z,theta,phi,frequency,speed,x0,y0,Lx,Ly,all_scat_stat)  #Scattering on this hole
            if hole_scattering_type != 'no_scattering':                         # If there was any scattering, then break the loop
                break

    if pillars == 'yes':
        for i in range(pillar_coordinates.shape[0]):                            # For each hole
            x0=pillar_coordinates[i,0]                                          # Coordinates of the hole center
            y0=pillar_coordinates[i,1]
            R=circular_hole_diameter*(1+pillar_coordinates[i,2])/2                # Radius of the given pillar
            theta,phi,pillar_scattering_type=scattering_on_circular_pillars(x,y,z,theta,phi,frequency,speed,x0,y0,R)
            if pillar_scattering_type != 'no_scattering':
                break
        
    # SCATTERING ON BOUNDARIES    
    theta,phi,wall_scattering_type=side_wall_scattering(x,y,z,theta,phi,frequency,speed)
    if pillars == 'yes':
        theta,phi,top_scattering_type=top_scattering_with_pillars(x,y,z,theta,phi,frequency,speed,pillar_coordinates)
    else:
        theta,phi,top_scattering_type=top_scattering(x,y,z,theta,phi,frequency,speed)
    theta,phi,bottom_scattering_type=bottom_scattering(x,y,z,theta,phi,frequency,speed)
    theta = theta-sign(theta)*2*pi*(abs(theta) > pi)                            # Check if theta became more than -pi:pi and return it bactk to this range
    surface_scattering_types = [wall_scattering_type, top_scattering_type, bottom_scattering_type, hole_scattering_type, pillar_scattering_type]
    return theta, phi, surface_scattering_types, all_scat_stat


def reinitialization(x, y, z, theta, phi, speed):
    '''Rethermalizing if the phonon comes back'''
    x1,y1,z1=move(x,y,z,theta,phi,speed)
    scattering_type='none'
    if y1<0:                                                                    # If the phonon returns to the staring line 
        #theta=arcsin(2*random()-1)                                             # Reinitialize with Lambert cosine distribution
        #phi=arcsin(2*random()-1)      
        theta=0.5*pi*(2*random()-1)                                             # Reinitialize with random distribution
        phi=0.5*pi*(2*random()-1)
        if hole_lattice_type=='serpentine':
            x=(-width/2+(155e-9)/2)+0.4*(155e-9)*(2*random()-1)
        elif hole_lattice_type=='diode_with_wires':
            x=0.4*(period_x-rectangular_hole_side_x)*(2*random()-1)
        elif hole_lattice_type=='turn':
            x=0.4*(period_x*5)*(2*random()-1)
        else:
            x=0.4*width*(2*random()-1)                                          # Reinitialize in random place
        z=0.4*thickness*(2*random()-1)
        scattering_type='diffuse'
    return theta, phi, scattering_type, x, y, z


def angle_distribution_calculation():
    '''This function analyses measured phonon angles and creates their distribution'''
    with open("All exit angles.txt", "r") as f:
        exit_angles = np.loadtxt(f, dtype='float')
    with open("All initial angles.txt", "r") as f:
        initial_angles = np.loadtxt(f, dtype='float')
    dist=zeros((180,3))
    dist[:,0]=range(-90,90)
    dist[:,1]=[len(filter(lambda x: x*180/pi >= j-0.5 and x*180/pi < j+0.5 and x!=0, exit_angles)) for j in dist[:,0]]
    dist[:,2]=[len(filter(lambda x: x*180/pi >= j-0.5 and x*180/pi < j+0.5 and x!=0, initial_angles)) for j in dist[:,0]]
    return dist


def free_path_distribution_calculation():
    '''This function analyses measured phonon free paths and creates their distribution'''
    with open("All free paths.txt","r") as f:
        free_paths = np.loadtxt(f, dtype='float')
    dist=zeros((number_of_nodes,2))
    dist[:,0]=[i*length/number_of_nodes for i in range(number_of_nodes)]  
    dist[:,1]=[len(filter(lambda x: x>=j-0.5*length/number_of_nodes and x<j+0.5*length/number_of_nodes and x!=0, free_paths)) for j in dist[:,0]]
    return dist


def travel_time_distribution_calculation():
    '''This function analyses measured travel times and creates their distribution'''
    with open("All travel times.txt","r") as f:
        travel_times = np.loadtxt(f, dtype='float')
    dist=zeros((number_of_nodes,2))
    dist[:,0]=[i*max(travel_times)/number_of_nodes for i in range(number_of_nodes)]  
    dist[:,1]=[len(filter(lambda x: x>=j-0.5*max(travel_times)/number_of_nodes and x<j+0.5*max(travel_times)/number_of_nodes and x!=0, travel_times)) for j in dist[:,0]]
    return dist


def frequency_distribution_calculation():
    '''This function analyses initial phonon frequncies and creates the frequancy spectrum'''
    with open("All frequencies.txt","r") as f:
        frequencies = np.loadtxt(f, dtype='float')
    max_f=np.amax(frequencies)
    dist=zeros((number_of_nodes,2))
    dist[:,0]=[i*max_f/number_of_nodes for i in range(number_of_nodes)]  
    dist[:,1]=[len(filter(lambda x: x>=j-0.5*max_f/number_of_nodes and x<j+0.5*max_f/number_of_nodes and x!=0, frequencies)) for j in dist[:,0]]
    return dist


def wavelength_distribution_calculation():
    '''This function calculates phonon wavelengths from their frequencies and velocities, and creates the wavelength spectrum'''
    with open("All frequencies.txt","r") as f:
        frequencies = np.loadtxt(f, dtype='float')
    with open("All group velocities.txt","r") as f:
        speeds = np.loadtxt(f, dtype='float')
    wavelengths=zeros((len(speeds)))
    wavelengths[:]=speeds[:]/frequencies[:]
    max_l=np.amax(wavelengths)
    dist=zeros((number_of_nodes,2))
    dist[:,0]=[i*max_l/number_of_nodes for i in range(number_of_nodes)]    
    dist[:,1]=[len(filter(lambda x: x>=j-0.5*max_l/number_of_nodes and x<j+0.5*max_l/number_of_nodes and x!=0, wavelengths)) for j in dist[:,0]]
    return dist


def scattering_events_statistics_calculation(statistics_of_scattering_events,surface_scattering_types,reinitialization_scattering_type,internal_scattering_type):
    '''This function analyzes type of scettering events and this timestep and adds them to the statistics'''
    statistics_of_scattering_events[0] += (surface_scattering_types[0] == 'diffuse')*1
    statistics_of_scattering_events[1] += (surface_scattering_types[0] == 'specular')*1   
    statistics_of_scattering_events[2] += (surface_scattering_types[1] == 'diffuse' or surface_scattering_types[2] == 'diffuse')*1
    statistics_of_scattering_events[3] += (surface_scattering_types[1] == 'specular' or surface_scattering_types[2] == 'specular')*1
    statistics_of_scattering_events[4] += (surface_scattering_types[3] == 'diffuse')*1
    statistics_of_scattering_events[5] += (surface_scattering_types[3] == 'specular')*1 
    statistics_of_scattering_events[6] += (reinitialization_scattering_type == 'diffuse')*1
    statistics_of_scattering_events[7] += (internal_scattering_type == 'diffuse')*1
    statistics_of_scattering_events[8] += (surface_scattering_types[4] == 'diffuse')*1
    statistics_of_scattering_events[9] += (surface_scattering_types[4] == 'specular')*1 
    return statistics_of_scattering_events


def maps_and_profiles_calculation(x,y,maps_and_profiles,phonon_properties,timestep_number,theta,phi):
    '''This function registers the phonon in the pixel corresponding to its curent position and at certain timesteps
    and calculates thermal maps and thermal profiles along different axes'''                                                            
    thermal_map, heat_flux_profile_x, heat_flux_profile_y, temperature_profile_x, temperature_profile_y = maps_and_profiles
    frequency, polarization, speed = phonon_properties[0:3]
    
    index_x = int(((x+width/2)*number_of_pixels_x) // width)                    # Calculate pixel numbers
    index_y = int((y*number_of_pixels_y) // length)
    Vcell_x=length*thickness*width/number_of_pixels_x                           # Volume of a unit cell
    Vcell_y=width*thickness*length/number_of_pixels_y
    
    if (index_x<number_of_pixels_x) and (index_y<number_of_pixels_y):           # This is to prevent error if the phonon is outside the structure 
        thermal_map[index_y,index_x] +=hbar*2*pi*frequency                      # Here we add the energy h*w to the pixel of the map
        
        #timeframe_number = int((timestep_number*timestep*number_of_timeframes) // (number_of_timesteps*timestep))
        
        timeframe_number = int(((timestep_number+randint(0, number_of_timesteps))*timestep*number_of_timeframes) // (number_of_timesteps*timestep))
        
        if timeframe_number < number_of_timeframes:
            heat_flux_profile_x[index_x,timeframe_number] += hbar*2*pi*frequency*cos(theta)*abs(cos(phi))*speed/Vcell_x
            heat_flux_profile_y[index_y,timeframe_number] += hbar*2*pi*frequency*cos(theta)*abs(cos(phi))*speed/Vcell_y
            temperature_profile_x[index_x,timeframe_number] += hbar*2*pi*frequency/(specific_heat_capacity*material_density)/Vcell_x
            temperature_profile_y[index_y,timeframe_number] += hbar*2*pi*frequency/(specific_heat_capacity*material_density)/Vcell_y
        
    maps_and_profiles = [thermal_map, heat_flux_profile_x, heat_flux_profile_y, temperature_profile_x, temperature_profile_y]
    return maps_and_profiles


def progress_bar(i, j, old_progress, scheme):
    '''This is a progress bar that outputs the progress each percent but not more often'''
    if scheme==1:
        progress=100*(i*number_of_phonons_in_a_group+j)//number_of_phonons
    elif scheme==2:
        progress=100*(i*number_of_phonons+j)//(number_of_phonons*3)
    if progress>old_progress:
        print "\r Progress -", progress, '%',
    return progress


def write_files(free_paths,free_paths_along_y,frequencies,exit_angles,initial_angles,group_velocities,statistics_of_scattering_events,all_travel_times,all_scat_stat):
    '''This function analyzes writes files with statistics'''
    os.chdir(output_folder_name)
    with open("All free paths.txt","w+") as f:
        f.writelines(["%s\n" % i for i in free_paths])
    with open("All free paths along y.txt","w+") as f:
        f.writelines(["%s\n" % i for i in free_paths_along_y])
    with open("All frequencies.txt","w+") as f:
        f.writelines(["%s\n" % i for i in frequencies])
    with open("All exit angles.txt","w+") as f:
        f.writelines(["%s\n" % i for i in exit_angles])
    with open("All initial angles.txt","w+") as f:
        f.writelines(["%s\n" % i for i in initial_angles])
    with open("All group velocities.txt","w+") as f:
        f.writelines(["%s\n" % i for i in group_velocities])    
    with  open("Statistics.txt","w+") as f:
        f.writelines(["%s\n" % i for i in statistics_of_scattering_events])
    with  open("All travel times.txt","w+") as f:
        f.writelines(["%s\n" % i for i in all_travel_times])
    with  open("All scattering angles.txt","w+") as f:
        f.writelines(["%s\n" % i for i in all_scat_stat])       
    return


def output_trajectories(x, y, z, N):
    '''This function outputs the phonon trajectories of N phonons'''
    for i in range(N): 
        plt.plot (np.trim_zeros(x[:,i])*1e6,np.trim_zeros(y[:,i])*1e6, linewidth=0.1)
    plt.xlabel('X (um)', fontsize=12)
    plt.ylabel('Y (um)', fontsize=12)
    plt.axes().set_aspect('equal', 'datalim')
    plt.savefig("Phonon paths XY.pdf",dpi=300, format = 'pdf', bbox_inches="tight")  
    plt.show()    
    for i in range(N): 
        plt.plot (np.trim_zeros(y[:,i])*1e6,np.trim_zeros(z[:,i])*1e6, linewidth=0.1)
    plt.xlabel('Y (um)', fontsize=12)
    plt.ylabel('Z (um)', fontsize=12)
    plt.axes().set_aspect('equal', 'datalim')
    plt.savefig("Phonon paths YZ.pdf",dpi=300, format = 'pdf', bbox_inches="tight")  
    plt.show()
    return


def output_thermal_map(thermal_map):
    '''This function outputs the thermal map'''
    from matplotlib.colors import LogNorm
    minimum_of_colorbar=1e-20                                                       # Cannot be zero!
    np.savetxt("Thermal Map.csv", thermal_map, delimiter=",")                   # First we write it into the file
    thermal_map=np.flipud(thermal_map)
    #plt.imshow(thermal_map, cmap='hot', interpolation='none', extent=[(-width/2)*1e6,(width/2)*1e6,0,length*1e6] )                # can also use interpolation='bicubic' and norm=LogNorm(vmin=0.01, vmax=np.amax(thermal_map))
    plt.imshow(thermal_map, cmap='hot', interpolation='none', extent=[(-width/2)*1e6,(width/2)*1e6,0,length*1e6], norm=LogNorm(vmin=minimum_of_colorbar, vmax=np.amax(thermal_map)) )
    plt.xlabel('X (um)', fontsize=12)
    plt.ylabel('Y (um)', fontsize=12)
    cbar=plt.colorbar()
    cbar.set_label('Energy density', rotation=90)
    plt.savefig("Thermal map.pdf",dpi=300, format = 'pdf', bbox_inches="tight")
    plt.show()
    return


def output_thermal_conductivity(maps_and_profiles):
    '''This function calculates the thermal conductivity from heat flux and temperature profiles'''
    thermal_map, J_profiles_x, J_profiles_y, T_profiles_x, T_profiles_y = maps_and_profiles
    thermal_conductivity=zeros((T_profiles_y.shape[1],2))
    thermal_conductivity[:,0]=range(T_profiles_y.shape[1])
    for i in range(T_profiles_y.shape[1]):
        dT=max(T_profiles_y[:,i])-min(T_profiles_y[:,i])
        J=sum(J_profiles_y[:,i])/J_profiles_y.shape[0]
        thermal_conductivity[i,1]=length*J/dT
    
    plt.plot (thermal_conductivity[:,0],thermal_conductivity[:,1], linewidth=1)
    plt.ylabel('Thermal conductivity (W/mK)', fontsize=12)
    plt.xlabel('Timestep', fontsize=12)
    plt.show()
    return 


def output_profiles(maps_and_profiles):
    '''This function outputs thermal and flux profiles along the structure'''
    thermal_map, J_profiles_x, J_profiles_y, T_profiles_x, T_profiles_y = maps_and_profiles
        
    coordinates_x=np.arange(T_profiles_x.shape[0])*1e6*width/T_profiles_x.shape[0]      # Let's create coordinate arrays (in um) 
    coordinates_y=np.arange(T_profiles_y.shape[0])*1e6*length/T_profiles_y.shape[0]
    
    np.savetxt("Temperature profiles x.csv", np.vstack((coordinates_x,T_profiles_x.T)).T, delimiter=",") # Saving all the profiles in the files
    np.savetxt("Temperature profiles y.csv", np.vstack((coordinates_y,T_profiles_y.T)).T, delimiter=",")
    np.savetxt("Heat flux profiles x.csv", np.vstack((coordinates_x,J_profiles_x.T)).T, delimiter=",")
    np.savetxt("Heat flux profiles y.csv", np.vstack((coordinates_y,J_profiles_y.T)).T, delimiter=",")
    #for i in range(T_profiles_x.shape[1]):                                      # Plotting and and saving the plots
    #    plt.plot (coordinates_x[:],T_profiles_x[:,i], linewidth=1)
    #plt.xlabel('X (um)', fontsize=12)
    #plt.ylabel('Temperature (K)', fontsize=12)
    #plt.show()
    for i in range(T_profiles_y.shape[1]):
        plt.plot (coordinates_y[:],T_profiles_y[:,i], linewidth=1)
    plt.xlabel('Y (um)', fontsize=12)
    plt.ylabel('Temperature (K)', fontsize=12)
    plt.show()
    #for i in range(J_profiles_x.shape[1]):
    #    plt.plot (coordinates_x[:],J_profiles_x[:,i], linewidth=1)
    #plt.xlabel('X (um)', fontsize=12)
    #plt.ylabel('Heat flux (W/m^2)', fontsize=12)
    #plt.show()
    for i in range(J_profiles_y.shape[1]):
        plt.plot (coordinates_y[:],J_profiles_y[:,i], linewidth=1)
    plt.xlabel('Y (um)', fontsize=12)
    plt.ylabel('Heat flux (W/m^2)', fontsize=12)
    plt.show()
    return


def output_distributions():
    '''This function outputs the distributions into the terminal and the folder'''
    angle_distributions=angle_distribution_calculation()             
    free_path_distribution=free_path_distribution_calculation()
    frequency_distribution=frequency_distribution_calculation()
    wavelength_distribution=wavelength_distribution_calculation()
    travel_time_distribution=travel_time_distribution_calculation()
    
    plt.plot (angle_distributions[:,0],angle_distributions[:,1],'b')
    plt.plot (angle_distributions[:,0],angle_distributions[:,2],'r')
    plt.xlabel('Angle (degree)', fontsize=12)
    plt.ylabel('Number of phonons', fontsize=12)
    plt.savefig("Distribution of angles.pdf", dpi=300, format = 'pdf', bbox_inches="tight")
    plt.show()
    np.savetxt('Distribution of angles.csv', angle_distributions, delimiter=",")
    
    plt.plot (free_path_distribution[:,0]*1e6,free_path_distribution[:,1])
    plt.xlabel('Free flights (um)', fontsize = 12)
    plt.ylabel('Number of flights', fontsize=12)
    plt.savefig("Distribution of free paths.pdf", dpi=300, format = 'pdf', bbox_inches="tight")
    plt.show()
    np.savetxt('Distribution of free paths.csv', free_path_distribution, delimiter=",")
    
    plt.plot (frequency_distribution[:,0],frequency_distribution[:,1])
    plt.xlabel('Frequency (Hz)', fontsize=12)
    plt.ylabel('Number of phonons', fontsize=12)
    plt.savefig("Distribution of frequencies.pdf", dpi=300, format = 'pdf', bbox_inches="tight")
    plt.show()
    np.savetxt('Distribution of frequencies.csv', frequency_distribution, delimiter=",")
    
    plt.plot (wavelength_distribution[:,0]*1e9,wavelength_distribution[:,1])
    plt.xlabel('Wavelength (nm)', fontsize=12)
    plt.ylabel('Number of phonons', fontsize=12)
    plt.savefig("Distribution of wavelengths.pdf", dpi=300, format = 'pdf', bbox_inches="tight")
    plt.show()
    np.savetxt('Distribution of wavelengths.csv', frequency_distribution, delimiter=",")
    
    plt.plot (travel_time_distribution[:,0]*1e9,travel_time_distribution[:,1])
    plt.xlabel('Travel time (ns)', fontsize=12)
    plt.ylabel('Number of phonons', fontsize=12)
    plt.savefig("Distribution of travel times.pdf", dpi=300, format = 'pdf', bbox_inches="tight")
    plt.show()
    np.savetxt('Distribution of travel times.csv', travel_time_distribution, delimiter=",")
    
    with open("All group velocities.txt","r") as f:
        speeds = np.loadtxt(f, dtype='float')    
    with open("All frequencies.txt","r") as f:
        frequencies = np.loadtxt(f, dtype='float')
    plt.plot (frequencies,speeds,'.')
    plt.xlabel('Frequency (Hz)', fontsize=12)
    plt.ylabel('Group velocity (m/s)', fontsize=12)
    plt.savefig("Group velocities.pdf", dpi=300, format = 'pdf', bbox_inches="tight")
    plt.show()
    return


def output_information(start_time, simulation_scheme):
    '''This function outputs the simulation information into the file in the folder'''
    with open("All exit angles.txt", "r") as f:
        exit_angles = np.loadtxt(f, dtype='float')
    percentage=100*np.count_nonzero(exit_angles)/(number_of_phonons+2*number_of_phonons*((simulation_scheme==2)*1))
    print "\n\r", percentage, '% of phonons reached the end of the system'
    print "The simulation took about", int((time.time()-start_time)//60), "min. to run"
    with open("Information.txt","w+") as f:
        f.writelines(['The simulation finished on %s' % time.strftime("%d %B %Y"),' at %s' % time.strftime("%H:%M"),' and took about %s min to run.' % int((time.time()-start_time)//60)])
        f.writelines(['\n \nNumber of phonons = %s' % number_of_phonons,'\nNumber of timesteps = %s' % number_of_timesteps,'\nLength of a timestep = %s s' % timestep,'\nTemperature = %s K' % T, ])
        f.writelines(['\n \nLength = %s m' % length,'\nWidth = %s m' % width,'\nThickness = %s m' % thickness])
        f.writelines(['\n \nSide wall roughness = %s m' % side_wall_roughness,'\nHole roughness = %s m' % hole_roughness,'\nTop roughness = %s m' % top_roughness,'\nBottom roughness = %s m' % bottom_roughness])
        f.writelines(['\n \nLattice type = % s' % hole_lattice_type,'\nPeriod in x direction = %s m' % period_x,'\nPeriod in y direction = %s m' % period_y])        
        f.writelines(['\nDiameter of the holes = %s m' % circular_hole_diameter])
        f.writelines(['\nHorizontal dimension of the holes = %s m' % rectangular_hole_side_x,'\nVertical dimension of the holes = %s m' % rectangular_hole_side_y])
        f.writelines(['\n \n%s' % percentage, '% of phonons reached the end of the system'])
    return


def output_statistics_on_scattering_events():
    '''This function calculated and outputs statistics on scattering events'''
    with open("Statistics.txt","r") as f:
        stat = np.loadtxt(f, dtype='float')
    with open("Information.txt","a") as f:
        avg_scat=np.sum(stat)/number_of_phonons
        scat_on_walls=100*(stat[0]+stat[1])/np.sum(stat)
        scat_on_walls_diff=100*stat[0]/(stat[0]+stat[1])
        scat_on_walls_spec=100*stat[1]/(stat[0]+stat[1])
        scat_on_topbot=100*(stat[2]+stat[3])/np.sum(stat)
        scat_on_topbot_diff=100*stat[2]/(stat[2]+stat[3])
        scat_on_topbot_spec=100*stat[3]/(stat[2]+stat[3])
        if holes == 'yes':
            scat_on_holes=100*(stat[4]+stat[5])/np.sum(stat)
            scat_on_holes_diff=100*stat[4]/(stat[4]+stat[5])
            scat_on_holes_spec=100*stat[5]/(stat[4]+stat[5])
        if pillars == 'yes':
            scat_on_pillars=100*(stat[8]+stat[9])/np.sum(stat)
            scat_on_pillars_diff=100*stat[8]/(stat[8]+stat[9])
            scat_on_pillars_spec=100*stat[9]/(stat[8]+stat[9])
        retherm=100*stat[6]/np.sum(stat)
        internal=100*stat[7]/np.sum(stat)
        f.writelines(['\n\nOn average, each phonon experienced %.2f scattering events' % avg_scat])
        f.writelines(['\n%.2f%% - scattering on side walls' % scat_on_walls,' (%.2f%% - diffuse,' % scat_on_walls_diff,' %.2f%% - specular)' % scat_on_walls_spec])
        f.writelines(['\n%.2f%% - scattering on top and bottom walls' % scat_on_topbot,' (%.2f%% - diffuse,' % scat_on_topbot_diff,' %.2f%% - specular)' % scat_on_topbot_spec])
        if holes == 'yes':
            f.writelines(['\n%.2f%% - scattering on hole walls' % scat_on_holes,' (%.2f%% - diffuse,' % scat_on_holes_diff,' %.2f%% - specular)' % scat_on_holes_spec])
        if pillars == 'yes':
            f.writelines(['\n%.2f%% - scattering on pillar walls' % scat_on_pillars,' (%.2f%% - diffuse,' % scat_on_pillars_diff,' %.2f%% - specular)' % scat_on_pillars_spec])
        f.writelines(['\n%.2f%% - rethermalization at the hot side' % retherm])
        f.writelines(['\n%.2f%% - internal scattering processes' % internal])
    os.remove("Statistics.txt")
    return


def run_one_phonon(phonon_properties, statistics_of_scattering_events, maps_and_profiles, all_scat_stat):
    '''This function runs one phonon through the system and returns its exit angle and its paths'''
    x=zeros((number_of_timesteps))
    y=zeros((number_of_timesteps))
    z=zeros((number_of_timesteps))
    frequency, polarization, speed = phonon_properties[0:3]
    x[0],y[0],z[0],theta,phi=initialization()                                   # We get initial x and z coordinates and angles for the phonon
    path_num=0
    free_paths=[0.0]
    free_paths_along_y=[0.0]
    time_since_previous_scattering=0.0                                                     
    initial_theta=theta
    exit_theta=0.0
    travel_time=0.0
    hole_coordinates,hole_shapes=hole_positioning(hole_lattice_type, rectangular_hole_side_y, width, period_x, period_y)
    pillar_coordinates=pillar_positioning(pillar_lattice_type, period_x, period_y)
    time_of_internal_scattering=internal_scattering_time_calculation(frequency,polarization)
    for i in range(1,number_of_timesteps): 
        internal_scattering_type='none'
        reinitialization_scattering_type='none'                                           
        if y[i-1]<length:                                                       # If the phonon is still in the system
            
            theta,phi,internal_scattering_type = internal_scattering(theta, phi, time_since_previous_scattering, time_of_internal_scattering)           
            theta,phi,surface_scattering_types,all_scat_stat = surface_scattering(x[i-1],y[i-1],z[i-1],theta,phi,frequency,hole_coordinates,hole_shapes,pillar_coordinates,speed,all_scat_stat)
            theta,phi,reinitialization_scattering_type,x[i-1],y[i-1],z[i-1] = reinitialization(x[i-1],y[i-1],z[i-1],theta,phi,speed)

            statistics_of_scattering_events = scattering_events_statistics_calculation(statistics_of_scattering_events,surface_scattering_types,reinitialization_scattering_type,internal_scattering_type)

            if internal_scattering_type != 'diffuse' and reinitialization_scattering_type != 'diffuse' and all(surface_scattering_types) != 'diffuse' :                                                  # If there was no scattering, we keep measuring the phonon path
                free_paths[path_num]+=speed*timestep
                if hole_lattice_type=='serpentine':
                    if abs(x[i-1])<(width/2-155e-9):
                        free_paths_along_y[path_num]+=speed*timestep*abs(cos(phi))*abs(sin(theta))
                    else:
                        free_paths_along_y[path_num]+=speed*timestep*abs(cos(phi))*abs(cos(theta))
                else:
                    free_paths_along_y[path_num]+=speed*timestep*abs(cos(phi))*abs(cos(theta))
                time_since_previous_scattering+=timestep
            else:                                                               # Otherwise, we start measuring phonon path from the beginning
                free_paths.append(0.0)
                free_paths_along_y.append(0.0)
                path_num+=1
                time_since_previous_scattering=0.0                               # And we reset the time without diffuse scattering 
                time_of_internal_scattering=internal_scattering_time_calculation(frequency, polarization)
            
            maps_and_profiles=maps_and_profiles_calculation(x[i-1],y[i-1],maps_and_profiles,phonon_properties,i,theta,phi)

            x[i],y[i],z[i]=move(x[i-1],y[i-1],z[i-1],theta,phi,speed)           # Phonon makes a step forward              
        else:                                                                   # If the phonon has reached the end of the system, break the loop
            exit_theta=theta
            travel_time=i*timestep                                         
            break
    flight_characteristics = [initial_theta, exit_theta, free_paths, free_paths_along_y, travel_time]
    return flight_characteristics, x, y, z, statistics_of_scattering_events, maps_and_profiles, all_scat_stat


def main1():
    '''This is the main function, which works under Debye approximation and should be used to simulate phonon paths at low temperatures'''
    print 'Simulation for',output_folder_name,'has began'
    simulation_scheme=1
    start_time=time.time()
    progress=-1
    
    all_initial_angles,all_exit_angles,all_free_paths,all_free_paths_along_y,all_frequencies,all_group_velocities,all_travel_times,all_scat_stat=([] for i in range(8)) 

    statistics_of_scattering_events=[0]*10
    thermal_map=zeros((number_of_pixels_y,number_of_pixels_x))
    heat_flux_profile_x=zeros((number_of_pixels_x,number_of_timeframes))
    heat_flux_profile_y=zeros((number_of_pixels_y,number_of_timeframes))
    temperature_profile_x=zeros((number_of_pixels_x,number_of_timeframes))
    temperature_profile_y=zeros((number_of_pixels_y,number_of_timeframes))
    maps_and_profiles=[thermal_map,heat_flux_profile_x,heat_flux_profile_y,temperature_profile_x,temperature_profile_y]
    
    for i in range(number_of_phonons/number_of_phonons_in_a_group):             # To reduce the memory load phonon are simulated in small groups
        x,y,z=(zeros((number_of_timesteps,number_of_phonons_in_a_group)) for i in range(3))
        for j in range(number_of_phonons_in_a_group):                                              
            progress=progress_bar(i,j,progress,simulation_scheme) 
            phonon_properties=phonon_properties_assignment()                    # We get initial phonon properties: frequency, polarization, and speed
            phonon_properties.append(i*number_of_phonons_in_a_group+j)          #we add phonon number to phonon properties
            
            flight_characteristics,x[:,j],y[:,j],z[:,j],statistics_of_scattering_events,maps_and_profiles,all_scat_stat = run_one_phonon(phonon_properties,statistics_of_scattering_events,maps_and_profiles,all_scat_stat)           
    
            all_initial_angles.append(flight_characteristics[0])    
            all_exit_angles.append(flight_characteristics[1])
            all_free_paths.extend(flight_characteristics[2])
            all_free_paths_along_y.extend(flight_characteristics[3])
            all_travel_times.append(flight_characteristics[4])
            all_frequencies.append(phonon_properties[0])
            all_group_velocities.append(phonon_properties[2])
            
    write_files(all_free_paths,all_free_paths_along_y,all_frequencies,all_exit_angles,all_initial_angles,all_group_velocities,statistics_of_scattering_events,all_travel_times,all_scat_stat)        
    output_distributions()
    output_thermal_map(maps_and_profiles[0])
    output_profiles(maps_and_profiles)
    output_thermal_conductivity(maps_and_profiles)
    output_trajectories(x,y,z,number_of_phonons_in_a_group)
    output_information(start_time, simulation_scheme)
    output_statistics_on_scattering_events()
    #coordinates=zeros((number_of_timesteps,number_of_phonons_in_a_group*3))
    return x,y,z


def main2():
    '''This is the main function, which calculates thermal conductivity by integrating bulk dispersion'''
    print 'Simulation for',output_folder_name,'has started'
    simulation_scheme=2
    start_time=time.time()
    progress=-1
    all_initial_angles,all_exit_angles,all_free_paths,all_free_paths_along_y,all_frequencies,all_group_velocities,all_travel_times,all_scat_stat=([] for i in range(8))
    statistics_of_scattering_events=[0]*10
    thermal_map=zeros((number_of_pixels_y,number_of_pixels_x))
    heat_flux_profile_x=zeros((number_of_pixels_x,number_of_timeframes))
    heat_flux_profile_y=zeros((number_of_pixels_y,number_of_timeframes))
    temperature_profile_x=zeros((number_of_pixels_x,number_of_timeframes))
    temperature_profile_y=zeros((number_of_pixels_y,number_of_timeframes))
    maps_and_profiles=[thermal_map,heat_flux_profile_x,heat_flux_profile_y,temperature_profile_x,temperature_profile_y]
    
    mean_free_path=zeros((number_of_phonons))
    thermal_conductivity=0
    cummulative_conductivity=zeros((number_of_phonons,6))
    for branch in range(3):                                                            # For each phonon branch
        x,y,z=(zeros((number_of_timesteps,number_of_phonons_in_a_group)) for i in range(3)) 
        for j in range(0,number_of_phonons):    
            progress=progress_bar(branch,j,progress,simulation_scheme)                                          
                                                   
            phonon_properties, w, K, dK  = phonon_properties_assignment_2(j,branch)
            
            flight_characteristics,x[:,j],y[:,j],z[:,j],statistics_of_scattering_events,maps_and_profiles,all_scat_stat = run_one_phonon(phonon_properties,statistics_of_scattering_events,maps_and_profiles,all_scat_stat)
            
            all_initial_angles.append(flight_characteristics[0])    
            all_exit_angles.append(flight_characteristics[1])
            all_free_paths.extend(flight_characteristics[2])
            all_free_paths_along_y.extend(flight_characteristics[3])
            all_travel_times.append(flight_characteristics[4])
            all_frequencies.append(phonon_properties[0])
            all_group_velocities.append(phonon_properties[2])
            
            
            frequency, polarization, speed = phonon_properties
            mean_free_path[j]=sum(flight_characteristics[2])/len(flight_characteristics[2])                       # Average of all free paths for this phonon
            heat_capacity=k*((hbar*w/(k*T))**2)*exp(hbar*w/(k*T))/((exp(hbar*w/(k*T))-1)**2) # Ref. PRB 88 155318 (2013)
            thermal_conductivity+=(1/(6*(pi**2)))*heat_capacity*(speed**2)*(mean_free_path[j]/speed)*(K**2)*dK   # Eq.3 from Physical Review 132 2461 (1963)
            
            cummulative_conductivity[j,branch]=speed/frequency
            cummulative_conductivity[j,branch+3]=(1/(6*(pi**2)))*heat_capacity*(speed**2)*(mean_free_path[j]/speed)*(K**2)*dK
            
    write_files(all_free_paths,all_free_paths_along_y,all_frequencies,all_exit_angles,all_initial_angles,all_group_velocities,statistics_of_scattering_events,all_travel_times,all_scat_stat) 
    output_trajectories(x,y,z,number_of_phonons)
    output_thermal_map(thermal_map)
    output_distributions()
    output_information(start_time, simulation_scheme)
    output_statistics_on_scattering_events()
    print 'Thermal conductivity =', thermal_conductivity
        
    for i in range(3):
        plt.loglog (cummulative_conductivity[:,i]*1e9,cummulative_conductivity[:,i+3])
    plt.show()
    np.savetxt('Distribution of wavelengths.txt', cummulative_conductivity, delimiter="	")
    return

main1()
