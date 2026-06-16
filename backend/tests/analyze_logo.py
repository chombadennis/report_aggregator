from PIL import Image
import numpy as np

img = Image.open('../frontend/public/neuralaxis-logo.png').convert('L')
data = np.array(img)

# Print average intensity per row to find the vertical range of the logo
row_means = np.mean(data, axis=1)
col_means = np.mean(data, axis=0)

# Print row indices where average intensity is above a threshold
threshold = 10  # adjust if needed
active_rows = np.where(row_means > threshold)[0]
active_cols = np.where(col_means > threshold)[0]

if len(active_rows) > 0:
    print(f"Active rows (above threshold {threshold}): from {active_rows[0]} to {active_rows[-1]}")
else:
    print("No active rows above threshold!")

if len(active_cols) > 0:
    print(f"Active cols (above threshold {threshold}): from {active_cols[0]} to {active_cols[-1]}")
else:
    print("No active cols above threshold!")

# Let's also find the bounding box of the circle by scanning from center
# Let's print row average around the middle (y=768)
print("Middle rows average intensity (row 700 to 800):")
print(row_means[700:800:10])
