from plansdk.apis.plan import Plan
import json
import math

class Activate(Plan):
    """activate a geometric-shape resource type"""

    def run(self):
        self.log("activate plan for pratik demo")

        # GET the resource its properties from the market as only the resource_id is passed in
        resource_id = self.params['resourceId']
        resource = self.bpo.resources.get(resource_id)
        properties = resource['properties']

        radius = properties['radius']
        sides = properties['sides']
        color = properties['color']

        circumference = math.pi * 2 * radius
        circleArea = math.pi * radius * radius

        sideLen = 2 * math.pi * (math.sin(math.pi/sides))
        perimeter = sides * sideLen
        polygonArea = ((sides * radius * radius)/2) * (math.sin((2 * math.pi)/sides))

        return {
            "color": color,
            "circumference": circumference,
            "totalArea": circleArea,
            "perimeter": perimeter,
            "polygonArea": polygonArea
        }

