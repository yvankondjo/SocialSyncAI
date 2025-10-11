import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

import requests

def test_get_user_profile():
    # Récupérer le profil d'un utilisateur Instagram via IGSID (Instagram Scoped ID)
    # Utilise l'API Facebook Graph pour Instagram Messenger Platform
    instagram_scoped_user_id = "1798889844048976"  # IGSID de l'utilisateur
    user_profile = requests.get(f'https://graph.instagram.com/v23.0/{instagram_scoped_user_id}\
?fields=name,username,profile_pic,follower_count,is_user_follow_business,is_business_follow_user\
&access_token=IGAAO2fA8GZAiJBZAFRpSDAtckhRaV9IaHNJUnZABam9jdGtacExzNVMxeng1S1ZAlZAm5lakNJNXhtQU1FYVRSeWt2a0lmY3VWYUF1QmZATOThBU203dktBUUlSMmxMRlRUQjNVTUpRUk1mcXJwcExRTXhPazJn')
    print(user_profile.json())

if __name__ == '__main__':
    test_get_user_profile()