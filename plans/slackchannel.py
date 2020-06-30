from plansdk.apis.plan import Plan
import requests
import json

class Activate(Plan):
    def run(self):
        resource_id = self.params['resourceId']
        resource = self.bpo.resources.get(resource_id)
        properties = resource['properties']
        label1 = properties['name']
        productId1 = properties['productid']

        [product] = self.bpo.market.get_products_by_resource_type('slackra_arjun.resourceTypes.Channels-create')
        childResource = self.bpo.resources.create(self.params['resourceId'],{"productId":product['id'],"label":label1,"properties" :{"name":label1}})
        print('####################################################')
        print(json.dumps(childResource))
        print('####################################################')
        response_data = { "id": childResource }
        # response_data = { "data": childResource }
        # print('####################################################')
        # print(json.dumps(response_data))
        # print('####################################################')
        return {"result_value": response_data}
