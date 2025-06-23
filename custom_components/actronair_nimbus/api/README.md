## Sample Request/Responses

### /api/v0/client

Method: GET
URL: https://nimbus.actronair.com.au/api/v0/client

#### Request

None

#### Response

```json
{
  "_links": {
    "account": { "href": "/api/v0/client/account", "title": "Account" },
    "ac-systems": {
      "href": "/api/v0/client/ac-systems",
      "title": "List of paired MWCs (QUE Only)"
    },
    "ac-systems-all": {
      "href": "/api/v0/client/ac-systems?includeAcms=true&includeNeo=true",
      "title": "List of paired AC systems (All Types)"
    },
    "user-devices": {
      "href": "/api/v0/client/user-devices",
      "title": "List of paired user devices"
    },
    "admin": {
      "href": "/api/v0/client/admin",
      "title": "User administration endpoint"
    },
    "customer-support": {
      "href": "/api/v0/client/support",
      "title": "Customer support endpoint"
    },
    "commands": {
      "href": "/api/v0/client/ac-systems/cmds/send?serial={wallControllerSerial}",
      "title": "Send commands to the paired AC System",
      "templated": true
    },
    "ac-latest-events": {
      "href": "/api/v0/client/ac-systems/events/latest?serial={wallControllerSerial}",
      "title": "Get the most recent events relating to the AC System",
      "templated": true
    },
    "ac-status": {
      "href": "/api/v0/client/ac-systems/status/latest?serial={wallControllerSerial}",
      "title": "Get the current status of the AC System",
      "templated": true
    },
    "reports": {
      "href": "/api/v0/client/reports",
      "title": "Get list of available reports"
    },
    "postcodes": {
      "href": "/api/v0/client/postcode?find={find}",
      "title": "Lookup information for a given postcode",
      "templated": true
    },
    "installer-lookup": {
      "href": "/api/v0/client/installers/{installerId}",
      "title": "GET the detail for a specific installer",
      "templated": true
    },
    "installer-image": {
      "href": "/api/v0/client/installers/{installerId}/image",
      "title": "GET the image for a speicifc installer",
      "templated": true
    },
    "installer-argb-image": {
      "href": "/api/v0/client/installers/{installerId}/image-argb",
      "title": "GET the ARGB image for a speicifc installer",
      "templated": true
    },
    "installers": {
      "href": "/api/v0/client/admin/installers",
      "title": "GET list of installers registered in the system"
    }
  }
}
```

### /api/v0/client/user-devices

Method: GET
URL: https://nimbus.actronair.com.au/api/v0/client/user-devices

#### Request

None

#### Resonse

```json
{
  "_links": {
    "user-device": [
      {
        "href": "/api/v0/client/user-devices/6Izsr_kRvwj-W82swXvGlQiqMPs5rTZIsJuwFKFm5mI%3D"
      },
      {
        "href": "/api/v0/client/user-devices/Dxab-YH30m099ux5Ie-0KdrjBd46N_7DUgBnwtjWh2k%3D"
      },
      {
        "href": "/api/v0/client/user-devices/JF2_JxFWoCmrOGAJ12BnPxfQFpRalG2MuBQ_RkQE9uY%3D"
      },
      {
        "href": "/api/v0/client/user-devices/PBDwYWDSH9rIvnS3BH-OdUC3R_wHhG2CoR4f7g7sKys%3D"
      },
      {
        "href": "/api/v0/client/user-devices/ZyAfBJ53Thxkd5XCr1deJs5D4JMAVoNmL66ccY65CKw%3D"
      }
    ]
  },
  "_embedded": {
    "user-device": [
      {
        "type": "Ios",
        "deviceName": "HomeAssistant",
        "id": "6Izsr_kRvwj-W82swXvGlQiqMPs5rTZIsJuwFKFm5mI=",
        "issued": "2025-02-20T09:53:56.9959723+00:00",
        "expires": "3025-02-20T09:53:56.9959723+00:00",
        "_links": {
          "self": {
            "href": "/api/v0/client/user-devices/6Izsr_kRvwj-W82swXvGlQiqMPs5rTZIsJuwFKFm5mI%3D"
          }
        }
      },
      {
        "type": "Android",
        "deviceName": "e1s",
        "id": "Dxab-YH30m099ux5Ie-0KdrjBd46N_7DUgBnwtjWh2k=",
        "issued": "2025-02-21T09:29:52.7992852+00:00",
        "expires": "3025-02-21T09:29:52.7992852+00:00",
        "_links": {
          "self": {
            "href": "/api/v0/client/user-devices/Dxab-YH30m099ux5Ie-0KdrjBd46N_7DUgBnwtjWh2k%3D"
          }
        }
      },
      {
        "type": "Ios",
        "deviceName": "HomeAssistant",
        "id": "JF2_JxFWoCmrOGAJ12BnPxfQFpRalG2MuBQ_RkQE9uY=",
        "issued": "2025-02-28T09:48:21.4799593+00:00",
        "expires": "3025-02-28T09:48:21.4799593+00:00",
        "_links": {
          "self": {
            "href": "/api/v0/client/user-devices/JF2_JxFWoCmrOGAJ12BnPxfQFpRalG2MuBQ_RkQE9uY%3D"
          }
        }
      },
      {
        "type": "Ios",
        "deviceName": "MyDevice",
        "id": "PBDwYWDSH9rIvnS3BH-OdUC3R_wHhG2CoR4f7g7sKys=",
        "issued": "2025-02-22T03:05:13.0437304+00:00",
        "expires": "3025-02-22T03:05:13.0437304+00:00",
        "_links": {
          "self": {
            "href": "/api/v0/client/user-devices/PBDwYWDSH9rIvnS3BH-OdUC3R_wHhG2CoR4f7g7sKys%3D"
          }
        }
      },
      {
        "type": "Ios",
        "deviceName": "HomeAssistant",
        "id": "ZyAfBJ53Thxkd5XCr1deJs5D4JMAVoNmL66ccY65CKw=",
        "issued": "2025-03-12T08:55:45.2953669+00:00",
        "expires": "3025-03-12T08:55:45.2953669+00:00",
        "_links": {
          "self": {
            "href": "/api/v0/client/user-devices/ZyAfBJ53Thxkd5XCr1deJs5D4JMAVoNmL66ccY65CKw%3D"
          }
        }
      }
    ]
  }
}
```

### /api/v0/client/ac-systems

Method: GET
URL: https://nimbus.actronair.com.au/api/v0/client/ac-systems?includeAcms=true&includeNeo=true

#### Request

None

#### Response

```json
{
  "_links": {
    "ac-system": {
      "href": "/api/v0/client/ac-systems/so_xxxybkPeYWzSleR_s8aaAs-9S1DnScvv7zanN6Pc%3D"
    }
  },
  "_embedded": {
    "ac-system": [
      {
        "type": "neo",
        "serial": "24i06570",
        "id": "so_xxxybkPeYWzSleR_s8aaAs-9S1DnScvv7zanN6Pc=",
        "issued": "2025-02-20T09:51:54.6479414+00:00",
        "expires": "3025-02-20T09:51:54.6479414+00:00",
        "description": "NEO_24I06570",
        "_links": {
          "self": {
            "href": "/api/v0/client/ac-systems/so_xxxybkPeYWzSleR_s8aaAs-9S1DnScvv7zanN6Pc%3D"
          },
          "commands": {
            "href": "/api/v0/client/ac-systems/cmds/send?serial=24i06570",
            "title": "Send commands to the paired AC System"
          },
          "force-disconnect": {
            "href": "/api/v0/client/ac-systems/cmds/force-disconnect?serial=24i06570",
            "title": "Force the specified AC System to reconnect"
          },
          "ac-status": {
            "href": "/api/v0/client/ac-systems/status/latest?serial=24i06570",
            "title": "Get the current status of the AC System"
          },
          "ac-latest-events": {
            "href": "/api/v0/client/ac-systems/events/latest?serial=24i06570",
            "title": "Get the most recent events relating to the AC System"
          }
        }
      }
    ]
  }
}
```
