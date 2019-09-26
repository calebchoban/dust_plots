from readsnap import readsnap
from dust_plots import *
from astropy.table import Table

# Load in halohistory data for main halo. All values should be in code units
halo_dir = './halos/'
halo_data = Table.read(halo_dir + 'halo_0000000.dat',format='ascii')
num = 588
snap_dir = './output'

H = readsnap(snap_dir, num, 0, header_only=1)
G = readsnap(snap_dir, num, 0)


xpos =  halo_data['col7'][num]
ypos =  halo_data['col8'][num]
zpos =  halo_data['col9'][num]
rvir = halo_data['col13'][num]
center = np.array([xpos,ypos,zpos])

coords = G['p']
# coordinates within a sphere of radius Rvir
in_sphere = np.power(coords[:,0] - center[0],2.) + np.power(coords[:,1] - center[1],2.) + np.power(coords[:,2] - center[2],2.) <= np.power(rvir,2.)
print len(G['rho'][in_sphere])
print np.sum(G['m'][in_sphere])


# Make phase plot
phase_plot(G,H,mask=in_sphere)
DZ_vs_dens(G,H,time=True,mask=in_sphere)