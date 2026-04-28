🚀 1. START STREAM API
Endpoint
POST http://52.64.157.221:6789/api/v1/live/streams/start
Headers
Authorization: Bearer <YOUR_TOKEN>
Content-Type: application/json
Request Body (START)
For GO2 (example)
{
  "deviceSn": "go2-001",
  "urlType": 1,
  "videoId": {
    "droneSn": "1581F7FVC25A700DF473",
    "payloadIndex": {
      "type": 99,
      "subType": 0,
      "position": 0
    },
    "videoType": "normal"
  },
  "videoQuality": 0,
  "videoType": "zoom",
  "missionId": "7dc50d8e-b328-4342-95eb-57e1c35ef7c4",
  "playbackUrl": ""
}
Expected Response (START)
{
  "code": 0,
  "message": "success",
  "data": {
    "streamId": "go2-001",
    "sessionId": "xxxx-xxxx-xxxx",
    "viewerCount": 1,
    "startTime": "2026-04-17 14:21:14",
    "canStop": true,
    "isSendHeartBeat": true
  }
}
🛑 2. STOP STREAM API
Endpoint
POST http://52.64.157.221:6789/api/v1/live/streams/stop
Headers
Authorization: Bearer <YOUR_TOKEN>
Content-Type: application/json
Request Body (STOP)

👉 First test with empty playbackUrl

{
  "deviceSn": "go2-001",
  "urlType": 1,
  "videoId": {
    "droneSn": "1581F7FVC25A700DF473",
    "payloadIndex": {
      "type": 99,
      "subType": 0,
      "position": 0
    },
    "videoType": "normal"
  },
  "videoQuality": 0,
  "videoType": "zoom",
  "missionId": "7dc50d8e-b328-4342-95eb-57e1c35ef7c4",
  "playbackUrl": ""
}
Expected Response (STOP)
{
  "deviceSn": "go2-001",
  "playbackUrl": "https://d1cljsnd3fjh7l.cloudfront.net/streams/.../index.m3u8",
  "siteName": "...",
  "deviceName": "...",
  "missionName": "...",
  "userName": "...",
  "startTime": "...",
  "endTime": "...",
  "totalTime": "...",
  "labelCounts": {},
  "bookmarks": []
}


## for adding new remote url in github
# first check 
git remote -v
# add
git remote add DhiveTeam git@github.com:DHiveTeam/robopilot_soak_test.git
# check again 
git remote -v 
# response
DhiveTeam       git@github.com:DHiveTeam/robopilot_soak_test.git (fetch)
DhiveTeam       git@github.com:DHiveTeam/robopilot_soak_test.git (push)
origin  git@github.com:ashwinmendhe-ui/robopilot_soak_test.git (fetch)
origin  git@github.com:ashwinmendhe-ui/robopilot_soak_test.git (push)

## then push 
git push DhiveTeam main

## if want to push any other remote url 
git push origin main

## or in both 
git push origin main && git push dhive main