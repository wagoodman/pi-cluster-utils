# Pi K8s Cluster Utilities

Requirements:
- some pi's with K8s installed and running
- an InkyPhat display attached to a single pi (where these utils run)

This repo provides two services:
- `inky.service`: a RPC server that accepts requests from other services/nodes to update the InkyPhat screen with content.
- `k8s-status.service`: a client to inky that monitors the status of K8s nodes and reports to the `inky.service` the status.

Why split these services up? Can't they be combined? Yes they can, however, I have other applications that are using the `inky.service` remotely to show auxillary information, so this architecture is useful for that purpose.