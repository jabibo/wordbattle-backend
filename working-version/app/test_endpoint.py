#!/usr/bin/env python3
import requests
import json

def test_endpoint():
    # Register a user first
    register_data = {
        'username': 'testuser123', 
        'email': 'test@example.com', 
        'password': 'testpass123'
    }
    response = requests.post('http://localhost:8000/users/register', json=register_data)
    print(f'Register: {response.status_code}')

    # Get auth token
    auth_data = {'username': 'testuser123', 'password': 'testpass123'}
    response = requests.post('http://localhost:8000/auth/token', data=auth_data)
    print(f'Auth: {response.status_code}')

    if response.status_code == 200:
        token = response.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        
        # Test the new endpoint
        game_data = {
            'language': 'en',
            'max_players': 2,
            'invitees': ['testuser123'],
            'base_url': 'http://localhost:8000'
        }
        
        response = requests.post('http://localhost:8000/games/create-with-invitations', 
                               json=game_data, headers=headers)
        print(f'Create game: {response.status_code}')
        print(f'Response: {response.text}')
    else:
        print('Failed to get auth token')

if __name__ == "__main__":
    test_endpoint() 