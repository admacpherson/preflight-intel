from app.pireps import fetch_pireps, compute_bbox

KORD = (41.97, -87.90)
KDEN = (39.85, -104.67)

bbox = compute_bbox(KORD, KDEN)
print(f"Bounding box: {bbox}\n")

pireps = fetch_pireps(bbox)
print(f"Total PIREPs returned: {len(pireps)}\n")

if pireps:
    print("=== First PIREP (all fields) ===")
    first = pireps[0]
    for key, value in first.items():
        print(f"  {key}: {value}")

    print(f"\n=== All {len(pireps)} PIREPs (summary) ===")
    for p in pireps:
        lat = p.get("latitude", "N/A")
        lon = p.get("longitude", "N/A")
        alt = p.get("altitude", "N/A")
        turb = p.get("turbulence", "N/A")
        ice = p.get("icing", "N/A")
        raw = p.get("rawOb", "N/A")
        print(f"  [{lat}, {lon}] alt={alt} turb={turb} ice={ice}")
        print(f"    raw: {raw}\n")
else:
    print("No PIREPs returned. Try expanding the bounding box or increasing lookback hours.")