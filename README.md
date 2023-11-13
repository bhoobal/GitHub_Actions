# GitHub_Actions

### Env variables:
Scope: Entire workflow Job, Step

Workflow level:

env:
  ARTIFACTORY_USERNAME: ${{ secrets.ARTIFACTORY_USERNAME }}
  ARTIFACTORY_PASSWORD: ${{ secrets.ARTIFACTORY_PASSWORD }}

Usage:
username: ${{ env.ARTIFACTORY_USERNAME }}

Step level
env:
DOCKER_IMAGE : demo/1.0.0
usage: in script
${DOCKER_IMAGE}

 <username>${env.ARTIFACTORY_USERNAME}</username>

      - name: Trigger Deployment 🎯
        if: env.RELEASED_VERSION != '' && inputs.trigger-deployment != ''
        uses:
        with: 
