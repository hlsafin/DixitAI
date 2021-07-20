from clarifai_grpc.channel.clarifai_channel import ClarifaiChannel
from clarifai_grpc.grpc.api import service_pb2_grpc
from clarifai_grpc.grpc.api import service_pb2, resources_pb2
from clarifai_grpc.grpc.api.status import status_code_pb2

import os
import json

def labelCards():
    stub = service_pb2_grpc.V2Stub(ClarifaiChannel.get_grpc_channel())

    file1 = open("api_key.txt","r+")  
    key = file1.readline()
    file1.close()

    file2 = open("data_path.txt","r+")  
    folder = file2.readline()
    file2.close()

    # This is how you authenticate.
    metadata = (('authorization', 'Key '+ key),)

    data = {}
    test_image = "https://pocket-image-cache.com/direct?url=https%3A%2F%2Fpocket-syndicated-images.s3.amazonaws.com%2F5d1625e19354f.jpg"

    for x,y in enumerate(os.listdir(folder)):
        if '.jpg' in y:
            # print(os.path.join(folder,y))
            image_path = os.path.join(folder,y)
            data[y] = []

            with open(image_path, "rb") as f:
                file_bytes = f.read()

            request = service_pb2.PostModelOutputsRequest(
                # This is the model ID of a publicly available General model. You may use any other public or custom model ID.
                model_id='aaa03c23b3724a16a56b629203edc62c',
                inputs=[
                resources_pb2.Input(data=resources_pb2.Data(image=resources_pb2.Image(base64=file_bytes)))
                ])
            response = stub.PostModelOutputs(request, metadata=metadata)

            if response.status.code != status_code_pb2.SUCCESS:
                raise Exception("Request failed, status code: " + str(response.status.code))

            for concept in response.outputs[0].data.concepts:
                print('%12s: %.2f' % (concept.name, concept.value))
                data[y].append((concept.name, concept.value))

    # print(data)

    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# labelCards()