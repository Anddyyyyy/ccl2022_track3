import argparse

# Apply the edits of a single annotator to generate the incorrected sentences.
def main(args):
	m2 = open(args.m2_file).read().strip().split("\n\n")
	out = open(args.out, "w")

	
	for sent in m2:
		sent = sent.split("\n")
		incor_sent = sent[0].split()[1:] # Ignore "S "
		out.write(" ".join(incor_sent)+"\n")

if __name__ == "__main__":
	# Define and parse program input
	parser = argparse.ArgumentParser()
	parser.add_argument("m2_file", help="The path to an input m2 file.")
	parser.add_argument("-out", help="A path to where we save the output incorrected text file.", required=True)
	parser.add_argument("-id", help="The id of the target annotator in the m2 file.", type=int, default=0)	
	args = parser.parse_args()
	main(args)