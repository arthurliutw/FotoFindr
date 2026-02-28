from deepface import DeepFace

def get_face_emotions(image_path: str):
    try:
        # 1. We use RetinaFace to FIND them (highest recall)
        # 2. We set align=True to straighten the face (CRITICAL for emotion)
        # 3. We use expand_percentage to give the emotion model more 'context'
        results = DeepFace.analyze(
            img_path=image_path, 
            actions=['emotion'],
            detector_backend='retinaface',
            align=True,
            expand_percentage=10  # Gives the model a bit more of the head/neck
        )
        return results
    except Exception as e:
        return {"error": str(e)}