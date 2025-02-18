from PIL import Image, ImageDraw, ImageFont, ImageOps
import ncnn
import numpy as np
import os
import cv2

class DetectedObject:
    @property
    def bounds(self):
        return Rect(round(self.xmin), round(self.ymin), round(self.xmax - self.xmin), round(self.ymax - self.ymin))

    def __init__(self, class_id: int, confidence: float, xmin: float, ymin: float, xmax: float, ymax: float, ):
        self.class_id = class_id
        self.confidence = confidence
        self.xmin = xmin
        self.ymin = ymin
        self.xmax = xmax
        self.ymax = ymax

    @property
    def class_name(self):
        return class_names[self.class_id]
        
    def __str__(self) -> str:
        return f"Object(class={self.class_name}, conf={round(100*self.confidence,2)}, Box ={self.bounds})"

    def __repr__(self) -> str:
        return str(self)

class Rect:
    def __init__(self, x: float, y: float, width: float, height: float):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    @property
    def size(self):
        return Size(self.width, self.height)
    
    @property
    def is_empty(self):
        return self.width <= 0 or self.height <= 0
    
    @property
    def origin(self):
        return Point(self.x, self.y)
    
    @property
    def center(self):
        return Point(self.x + self.width / 2, self.y + self.height / 2)
    
    @property
    def area(self):
        return self.width * self.height
    
    def contains(self, point):
        return self.x <= point.x <= self.x + self.width and self.y <= point.y <= self.y + self.height
    
    def __str__(self) -> str:
        return f'{{x: {self.x}, y: {self.y}, w: {self.width}, h: {self.height}}}'
    
    def __repr__(self) -> str:
        return str(self)
    
class Size:
    def __init__(self, width: float, height: float):
        self.width = width
        self.height = height

class Point:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

# Confidence conf
# Non-max suppression conf
nms_threshold = 0.7
# Set the input image size

class_names = ['Stop sign', 'Parking sign', 'Priority sign', 'Crosswalk sign', 'Highway entrance sign', 'Highway exit sign','Round-about sign','One way road sign', 'No-entry road sign'] 

imagepath = r"D:\Projects\Bosch\Sign Detection\Scripts\Testing\Manual test\Parking_sign_556.jpg"

net = ncnn.Net()

# Load NCNN the model file
curr_dir = os.path.dirname(__file__)
net.load_param(os.path.join(curr_dir, 'best_ncnn_model', 'model.ncnn.param'))
net.load_model(os.path.join(curr_dir, 'best_ncnn_model', 'model.ncnn.bin'))

def ncnn_inference(image, target_size=320, conf=0.5):
    frame = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    # Open the image using PIL
    with Image.fromarray(frame) as img:
        # We'll be letterboxing the image to fit the target size
        longer_side = max(img.size[0], img.size[1])
        # Note the scale factor so we can expand the detection coordinates back to the original image size
        scale = longer_side / target_size
        # Since the image is letterboxed we'll need to note the padding offset
        offset_x = (longer_side - img.size[0]) // 2
        offset_y = (longer_side - img.size[1]) // 2
        # Scale and letterbox the image
        scaled_img = preprocess_image(img, target_size)
    
    # Convert the image to NCNN Mat (setting the pixel format to PIXEL_RGB yielded identical result as PIXEL_BGR)
    image = ncnn.Mat.from_pixels(np.asarray(scaled_img), ncnn.Mat.PixelType.PIXEL_BGR, scaled_img.width, scaled_img.height)
    mean = [0, 0, 0]
    std = [1/255, 1/255, 1/255]
    # Normalize the image
    image.substract_mean_normalize(mean=mean, norm=std)
    extractor = net.create_extractor()
    extractor.set_light_mode(True)
    extractor.input("in0", image)
    out = ncnn.Mat()
    # Run the inference
    extractor.extract("out0", out)
    out = np.asarray(out)

    candidates = []
    for i in range(len(out[0])):
        cx, cy = out[0][i], out[1][i]
        w, h = out[2][i], out[3][i]
        scores = out[4:]  # Get all class scores
        class_id = np.argmax(scores[:, i])  # Get the class with the highest score
        score = scores[class_id, i]  # The confidence score for the best class
        
        if score > conf:  # Check if the confidence exceeds the conf
            # Convert the center and width/height to left, top, right, and bottom
            candidates.append([score, cx-w/2, cy-h/2, cx+w/2, cy+h/2, w*h, class_id])

    extractor.clear()

    # Sort the detection on confidence
    candidates.sort(key=lambda x: x[0], reverse=True)
    # Convert to a list of DetectedObject instances
    detections = list(map(lambda x: DetectedObject(x[6], x[0], x[1] * scale - offset_x, x[2] * scale - offset_y, x[3] * scale - offset_x, x[4] * scale - offset_y), candidates))
    # Apply non-maximum suppression and filter out detections below the confidence conf
    detections = list(filter(lambda x: x.confidence >= conf, nms(detections)))

    return detections

def preprocess_image(image, target_size):
    img = image.convert("RGB")
    old_size = img.size
    ratio = float(target_size)/max(old_size)
    new_size = tuple([int(x*ratio) for x in old_size])
    img = img.resize(new_size, Image.BICUBIC)
    with Image.new("RGB", (target_size, target_size)) as new_img:
        new_img.paste(img, ((target_size-new_size[0])//2, (target_size-new_size[1])//2))
    return new_img

def nms(boxes):
    boxes.sort(key=lambda x: x.confidence, reverse=True)
    selected = []
    active = [True] * len(boxes)
    num_active = len(active)
    done = False
    i = 0
    while i < len(boxes) and not done:
        if active[i]:
            box_a = boxes[i]
            selected.append(box_a)
            if len(selected) >= 20:
                break
            for j in range(i+1, len(boxes)):
                if active[j]:
                    box_b = boxes[j]
                    if iou(box_a.bounds, box_b.bounds) > nms_threshold:
                        active[j] = False
                        num_active -= 1
                        if num_active <= 0:
                            done = True
                            break
        i += 1
    return selected

def iou(a: Rect, b: Rect) -> float:
    area_a = a.area
    if area_a <= 0:
        return 0.0
    area_b = b.area
    if area_b <= 0:
        return 0.0
    intersection_min_x = max(a.x, b.x)
    intersection_min_y = max(a.y, b.y)
    intersection_max_x = min(a.x + a.width, b.x + b.width)
    intersection_max_y = min(a.y + a.height, b.y + b.height)
    intersection_area = max(intersection_max_x - intersection_min_x, 0) * max(intersection_max_y - intersection_min_y, 0)
    return intersection_area / (area_a + area_b - intersection_area)

def draw_detections(image, detections, display=False):
    with Image.fromarray(image) as img:
        draw = ImageDraw.Draw(img)
        for detection in detections:
            box = detection.bounds
            draw.rectangle([box.x, box.y, box.x + box.width, box.y + box.height], outline="red", width=3)
            label = f"{detection.class_name} ({round(detection.confidence * 100, 2)}%)"
            draw.text((box.x-10, box.y-10), label, fill="red")
        if display:
            img.show()
        return img


if __name__ == '__main__':
    outputs = ncnn_inference(imagepath)
    for output in outputs:
        print(f"{output}")

    # Draw the detections on the image and display it
    draw_detections(imagepath, outputs)
