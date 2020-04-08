from readsnap import readsnap
from dust_plots import *
from astropy.table import Table
import os
import subprocess



main_dir = '/oasis/tscc/scratch/cchoban/non_cosmological_runs/Species/'
names = ['fiducial_model','elem_creation_eff','enhanced_acc','extra_O']
snap_dirs = [main_dir + i + '/output/' for i in names] 
labels = ['Fiducial','Elem. Creation Eff.','Enhanced Acc.','Enhanced O']
image_dir = './non_cosmo_species_images/'
sub_dir = 'compare_snapshots/' # subdirectory 

implementation = 'species'

cosmological = False

# First create ouput directory if needed
try:
    # Create target Directory
    os.mkdir(image_dir)
    print "Directory " + image_dir +  " Created " 
except:
    print "Directory " + image_dir +  " already exists"
try:
    # Create target Directory
    os.mkdir(image_dir + sub_dir)
    print "Directory " + image_dir + sub_dir + " Created " 
except:
    print "Directory " + image_dir + sub_dir + " already exists"


# List of snapshots to compare
snaps = [100,200,300]

# Maximum radius used for getting data
r_max_phys = 20 # kpc

for i, num in enumerate(snaps):
	print(num)
	Gas_snaps = []; Headers = []; masks = []; centers = []; r_maxes = [];
	for j,snap_dir in enumerate(snap_dirs):
		name = names[j]
		print(name)

		H = readsnap(snap_dir, num, 0, header_only=1, cosmological=cosmological)
		Headers += [H]
		G = readsnap(snap_dir, num, 0, cosmological=cosmological)
		Gas_snaps += [G]

		# Since this is a shallow copy, this fixes G['p'] as well
		coords = G['p']
		# Recenter coords at center of periodic box
		boxsize = H['boxsize']
		mask1 = coords > boxsize/2; mask2 = coords <= boxsize/2
		# This also changes G['p'] as well
		coords[mask1] -= boxsize/2; coords[mask2] += boxsize/2; 
		center = np.average(coords, weights = G['m'], axis = 0)
		centers += [center]
		
		# coordinates within a sphere of radius r_max_phys
		r_maxes += [r_max_phys]


	# Make D/Z vs r plot
	DZ_vs_r(Gas_snaps, Headers, centers, r_maxes, bin_nums=50, time=True, foutname=image_dir+sub_dir+implementation+'_DZ_vs_r_snapshot_%03d.png' % num,labels=labels,cosmological=cosmological)
	# Make D/Z vs density plot
	DZ_vs_dens(Gas_snaps,Headers, centers, r_maxes, time=True, foutname=image_dir+sub_dir+implementation+'_compare_DZ_vs_dens_snapshot_%03d.png' % num,labels=labels,cosmological=cosmological)
	# Make D/Z vs Z plot
	DZ_vs_Z(Gas_snaps,Headers, centers, r_maxes, time=True, Zmin=1E0, Zmax=1e1,foutname=image_dir+sub_dir+implementation+'_compare_DZ_vs_Z_snapshot_%03d.png' % num,labels=labels,cosmological=cosmological)

	DZ_vs_all(Gas_snaps,Headers, centers, r_maxes, bin_nums=50, time=True, depletion=False, cosmological=cosmological, labels=labels, \
			  foutname=image_dir+sub_dir+implementation+'_compare_DZ_vs_all_snapshot_%03d.png' % num, std_bars=True, style='color', nHmin=1E-3, nHmax=1E3, Zmin=1E0, Zmax=1E1)
			