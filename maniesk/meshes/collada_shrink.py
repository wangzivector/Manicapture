import collada

# Load the DAE file
dae = collada.Collada("p1.dae")

# Loop through all geometries
for geom in dae.geometries:
    for prim in geom.primitives:
        # Scale vertex positions by 1000 (meters → millimeters)
        prim.vertex[:] *= 0.001

# Save the modified file
dae.write("p1.dae")

print("Conversion complete: p1.dae saved.")
