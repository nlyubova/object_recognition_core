#!/usr/bin/env python
"""
Module defining the TOD detector to find objects in a scene
""" 

import ecto
from feature_descriptor import FeatureDescriptor
from ecto_object_recognition import capture, tod_detection
from ecto_opencv import calib

########################################################################################################################

class TodDetector(ecto.BlackBox):
    def __init__(self, plasm, feature_descriptor_params, db_json_params, object_ids, search_json_params,
                 guess_json_params):
        ecto.BlackBox.__init__(self, plasm)

        self._db_json_params = db_json_params
        self._object_ids = object_ids
        self._guess_json_params = guess_json_params

        # parse the JSON and load the appropriate feature descriptor module
        self.feature_descriptor = FeatureDescriptor(feature_descriptor_params)
        self.descriptor_matcher = tod_detection.DescriptorMatcher("Matcher", db_json_params=db_json_params, object_ids=object_ids,
                                                        search_json_params=search_json_params)
        self.guess_generator = tod_detection.GuessGenerator("Guess Gen",json_params=guess_json_params)
        self._rescale_depth = capture.RescaledRegisteredDepth()
        self._image_duplicator = ecto.Passthrough()
        self._depth_to_3d = calib.DepthTo3d()

    def expose_inputs(self):
        return {'image': self._image_duplicator['in'],
                'mask': self.feature_descriptor['mask'],
                'K': self._depth_to_3d['K'],
                'depth': self._rescale_depth['depth']}

    def expose_outputs(self):
        return {'object_ids': self.guess_generator['object_ids'],
                'Rs': self.guess_generator['Rs'],
                'Ts': self.guess_generator['Ts'],
                'keypoints': self.feature_descriptor['keypoints']}

    def expose_parameters(self):
        return {'db_json_params': self._db_json_params,
                'guess_json_params': self._guess_json_params,
                'object_ids': self._object_ids
                }

    def connections(self):
        connections = [self._image_duplicator[:] >> self.feature_descriptor['image'],
                       self._image_duplicator[:] >> self._rescale_depth['image']]
        connections += [self._rescale_depth['depth'] >> self._depth_to_3d['depth']]
        connections += [self.feature_descriptor['keypoints'] >> self.guess_generator['keypoints'],
                self.feature_descriptor['descriptors'] >> self.descriptor_matcher['descriptors'],
                self.descriptor_matcher['matches'] >> self.guess_generator['matches'],
                self.descriptor_matcher['matches_3d'] >> self.guess_generator['matches_3d'],
                self._depth_to_3d['points3d'] >> self.guess_generator['points3d']]
        return connections
