from common.utils.attack_utils import ScanStatus
from monkey_island.cc.database import mongo
from monkey_island.cc.services.attack.technique_reports import AttackTechnique


class T1082(AttackTechnique):
    tech_id = "T1082"
    relevant_systems = ["Linux", "Windows"]
    unscanned_msg = "Monkey didn't gather any system info on the network."
    scanned_msg = ""
    used_msg = "Monkey gathered system info from machines in the network."

    query = [
        {"$match": {"telem_category": "system_info", "data.network_info": {"$exists": True}}},
        {
            "$project": {
                "machine": {"hostname": "$data.hostname", "ips": "$data.network_info.networks"},
                "aws": "$data.aws",
                "process_list": "$data.process_list",
                "ssh_info": "$data.ssh_info",
                "azure_info": "$data.Azure",
            }
        },
        {
            "$project": {
                "_id": 0,
                "machine": 1,
                "collections": [
                    {
                        "used": {"$and": [{"$gt": ["$aws", {}]}]},
                        "name": {"$literal": "Amazon Web Services info"},
                    },
                    {
                        "used": {
                            "$and": [
                                {"$ifNull": ["$process_list", False]},
                                {"$gt": ["$process_list", {}]},
                            ]
                        },
                        "name": {"$literal": "Running process list"},
                    },
                    {
                        "used": {
                            "$and": [{"$ifNull": ["$ssh_info", False]}, {"$ne": ["$ssh_info", []]}]
                        },
                        "name": {"$literal": "SSH info"},
                    },
                    {
                        "used": {
                            "$and": [
                                {"$ifNull": ["$azure_info", False]},
                                {"$ne": ["$azure_info", []]},
                            ]
                        },
                        "name": {"$literal": "Azure info"},
                    },
                    {"used": True, "name": {"$literal": "Network interfaces"}},
                ],
            }
        },
        {"$group": {"_id": {"machine": "$machine", "collections": "$collections"}}},
        {"$replaceRoot": {"newRoot": "$_id"}},
    ]

    @staticmethod
    def get_report_data():
        def get_technique_status_and_data():
            system_info = list(mongo.db.telemetry.aggregate(T1082.query))
            if system_info:
                status = ScanStatus.USED.value
            else:
                status = ScanStatus.UNSCANNED.value
            return (status, system_info)

        status, system_info = get_technique_status_and_data()
        data = {"title": T1082.technique_title()}
        data.update({"system_info": system_info})

        data.update(T1082.get_mitigation_by_status(status))
        data.update(T1082.get_message_and_status(status))
        return data
