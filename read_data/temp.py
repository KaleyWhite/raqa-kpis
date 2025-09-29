import requests
data = requests.get(
    'https://radformation.com/api/internal/product-data/stats/RadMachine?fromDate=2025-09-26',
    headers={
        'authorization': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6NjI4NDM3ODIwODUzNDUyOH0.Zgd_RpZH2fY4iOpKxKSAiBz4C3o8R7E3-L_VbHTatso'
    }
)
print(data)