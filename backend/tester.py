import json
from pipeline.faces import get_face_emotions

def main():
    test_image = "test.jpg"  # Make sure this file exists in your folder!
    
    print(f"--- Testing DeepFace on {test_image} ---")
    
    results = get_face_emotions(test_image)
    
    if isinstance(results, dict) and "error" in results:
        print(f"❌ Error: {results['error']}")
    else:
        print(f"✅ Success! Found {len(results)} face(s).\n")
        
        for i, face in enumerate(results):
            emotion = face['dominant_emotion']
            confidence = face['emotion'][emotion]
            
            print(f"Face {i+1}:")
            print(f"  - Dominant Emotion: {emotion}")
            print(f"  - Confidence: {confidence:.2f}%")
            print(f"  - Face Location: {face['region']}")
            print("-" * 20)

if __name__ == "__main__":
    main()