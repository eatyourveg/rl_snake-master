import numpy as np

# Load the file
data = np.load("./logs/results/evaluations.npz")

# Print the keys available inside the archive
print(data.files) 
# Output: ['timesteps', 'results', 'ep_lengths']

print("Checkpoints evaluated at timesteps:", data['timesteps'])
print("Evaluation rewards history:", data['results'])