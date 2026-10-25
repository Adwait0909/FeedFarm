def owns_cow(cursor, farmer_id, cow_id):
    """Return True if the cow_id belongs to farmer_id."""
    cursor.execute("SELECT 1 FROM cows WHERE cow_id = %s AND farmer_id = %s LIMIT 1", (cow_id, farmer_id))
    return cursor.fetchone() is not None

def owns_farm(cursor, farmer_id, farm_id):
    cursor.execute("SELECT 1 FROM farms WHERE farm_id = %s AND farmer_id = %s LIMIT 1", (farm_id, farmer_id))
    return cursor.fetchone() is not None
