# Model workspace

Do not commit large model binaries to Git. Commit model descriptions, dataset versions, training parameters, metrics, and export instructions only. Store large local artifacts outside Git or attach them to a release when a later deployment phase is approved.

- `onnx/`: intermediate ONNX exports.
- `exported/`: converter outputs and packaging artifacts.
- `maixcam/`: final MaixCAM-ready local models.

No model has been trained or deployed for the current 2025E loop.
