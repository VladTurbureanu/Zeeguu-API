import numpy
import matplotlib.pylab as plt

def generate_matrix_visualization(known_words):

	m = []
	for i in range(0,100):
		m.append([])
		for j in range (0, 100):
			if (i*100+j) in known_words:
				m[i].append(1)
			else:
				m[i].append(0.65)
	
	# we need this next line to scale the color scheme
	m[0][0]=0

	matrix = numpy.matrix(m)


	fig = plt.figure()
	ax = fig.add_subplot(1,1,1)
	ax.set_aspect('equal')
	plt.imshow(matrix, interpolation='none')
	plt.colorbar()
	plt.show()


# assume known words in current folder words.txt file
known_words = []

with open ('words.txt') as f:
	for line in f: 
		known_words.append(int	(line))

generate_matrix_visualization(known_words)
