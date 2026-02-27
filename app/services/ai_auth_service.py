import torch
import numpy as np
from facenet_pytorch import MTCNN, InceptionResnetV1
from PIL import Image
from scipy.spatial.distance import cosine
import io


class FaceAuthService:

    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        self.mtcnn = MTCNN(image_size=160, margin=0, device=self.device)

        self.model = InceptionResnetV1(pretrained='vggface2').eval().to(self.device)

    def get_embedding(self, image_bytes: bytes):

        image = Image.open(io.BytesIO(image_bytes)).convert('RGB')

        face = self.mtcnn(image)

        if face is None:
            return None

        face = face.unsqueeze(0).to(self.device)

        with torch.no_grad():
            embedding = self.model(face)

        return embedding.squeeze().cpu().numpy()

    def compare_faces(self, emb1, emb2, threshold=0.6):

        emb1 = np.array(emb1)
        emb2 = np.array(emb2)

        similarity = 1 - cosine(emb1, emb2)

        return similarity > threshold, similarity


face_auth_service = FaceAuthService()
