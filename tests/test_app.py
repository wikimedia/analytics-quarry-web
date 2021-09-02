def test_frontpage(client, redisdb):
    rv = client.get("/")
    print(rv.__dict__)
    assert rv.status_code == 200
    assert rv.data
