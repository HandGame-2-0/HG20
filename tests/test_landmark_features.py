import numpy as np
import pytest

from handgame.recognition.landmark_features import (
    FEATURE_SIZE,
    HAND_GEOMETRY_SIZE,
    LEFT_HAND,
    PALM_VOLUME_SIZE,
    RIGHT_HAND,
    hand_geometry_features,
    landmarks_to_features,
    palm_volume_features,
)


def _hand(seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.uniform(100.0, 300.0, size=(21, 3))


def test_feature_vector_shape_and_wrist_origin():
    features = landmarks_to_features(_hand(), RIGHT_HAND)
    assert features.shape == (FEATURE_SIZE,)
    assert features.dtype == np.float32
    np.testing.assert_allclose(features[:3], 0.0)


def test_invariant_to_translation_and_scale():
    hand = _hand()
    moved = hand * 2.5 + np.array([40.0, -15.0, 3.0])
    np.testing.assert_allclose(
        landmarks_to_features(hand, RIGHT_HAND),
        landmarks_to_features(moved, RIGHT_HAND),
        atol=1e-5,
    )


def test_left_hand_is_mirrored_onto_right_layout():
    right = _hand()
    left = right.copy()
    left[:, 0] = -left[:, 0]
    np.testing.assert_allclose(
        landmarks_to_features(left, LEFT_HAND),
        landmarks_to_features(right, RIGHT_HAND),
        atol=1e-5,
    )


def test_degenerate_hand_does_not_divide_by_zero():
    features = landmarks_to_features(np.ones((21, 3)), RIGHT_HAND)
    assert np.all(np.isfinite(features))


def test_rejects_wrong_shape():
    with pytest.raises(ValueError):
        landmarks_to_features(np.zeros((20, 3)))
    with pytest.raises(ValueError):
        palm_volume_features(np.zeros((20, 3)))


def _reference_palm_volumes(world: np.ndarray) -> np.ndarray:
    """Straight port of handgesture ``extract_all_volumes``."""
    p0, p5, p17 = world[0], world[5], world[17]
    scale = np.linalg.norm(p17 - p5)
    return np.array(
        [
            np.dot(np.cross(p5 - p0, p17 - p0), world[i] - p0) / 6.0 / scale**3
            for i in (1, 2, 3, 4, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 18, 19, 20)
        ]
    )


def _rotation(seed: int) -> np.ndarray:
    q, _ = np.linalg.qr(np.random.default_rng(seed).normal(size=(3, 3)))
    return q * np.sign(np.linalg.det(q))  # proper rotation, det = +1


def test_palm_volumes_match_handgesture_reference():
    world = np.random.default_rng(3).normal(0.0, 0.05, (21, 3))
    features = palm_volume_features(world, RIGHT_HAND)
    assert features.shape == (PALM_VOLUME_SIZE,) and features.dtype == np.float32
    np.testing.assert_allclose(features, _reference_palm_volumes(world), rtol=1e-5, atol=1e-7)


def test_palm_volumes_invariant_to_pose_and_hand_size():
    world = np.random.default_rng(4).normal(0.0, 0.05, (21, 3))
    moved = 1.7 * world @ _rotation(5).T + np.array([0.3, -0.1, 0.2])
    np.testing.assert_allclose(
        palm_volume_features(moved, RIGHT_HAND),
        palm_volume_features(world, RIGHT_HAND),
        rtol=1e-4,
        atol=1e-6,
    )


def test_palm_volumes_left_hand_matches_mirrored_right_hand():
    right = np.random.default_rng(6).normal(0.0, 0.05, (21, 3))
    left = right * np.array([-1.0, 1.0, 1.0])
    np.testing.assert_allclose(
        palm_volume_features(left, LEFT_HAND),
        palm_volume_features(right, RIGHT_HAND),
        rtol=1e-5,
        atol=1e-7,
    )


def test_palm_volumes_degenerate_hand_is_finite():
    assert np.all(np.isfinite(palm_volume_features(np.zeros((21, 3)))))
    assert np.all(np.isfinite(hand_geometry_features(np.zeros((21, 3)))))


def test_hand_geometry_extends_volumes_with_normalized_distances():
    world = np.random.default_rng(7).normal(0.0, 0.05, (21, 3))
    features = hand_geometry_features(world, RIGHT_HAND)
    assert features.shape == (HAND_GEOMETRY_SIZE,) and features.dtype == np.float32
    np.testing.assert_allclose(features[:PALM_VOLUME_SIZE], palm_volume_features(world, RIGHT_HAND))
    palm_width = np.linalg.norm(world[17] - world[5])
    # pair (0, 1) comes first, pair (19, 20) last
    assert features[PALM_VOLUME_SIZE] == pytest.approx(
        np.linalg.norm(world[0] - world[1]) / palm_width, rel=1e-5
    )
    last = np.linalg.norm(world[19] - world[20]) / palm_width
    assert features[-1] == pytest.approx(last, rel=1e-5)


def test_hand_geometry_invariant_to_pose_size_and_hand():
    world = np.random.default_rng(8).normal(0.0, 0.05, (21, 3))
    moved = 0.6 * world @ _rotation(9).T + np.array([0.1, 0.2, -0.3])
    mirrored = world * np.array([-1.0, 1.0, 1.0])
    reference = hand_geometry_features(world, RIGHT_HAND)
    moved_features = hand_geometry_features(moved, RIGHT_HAND)
    mirrored_features = hand_geometry_features(mirrored, LEFT_HAND)
    np.testing.assert_allclose(moved_features, reference, rtol=1e-4, atol=1e-6)
    np.testing.assert_allclose(mirrored_features, reference, rtol=1e-5, atol=1e-7)
