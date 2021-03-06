from typing import List

import utils
import instance
from backend import RuntimeFailure

LOG = utils.get_logger(__file__)


def algo(inst: instance.Instance):
    # get all possible points
    points = utils.get_scan_path(inst.x_size, inst.y_size, inst.radius)  # inst.all_points

    for i, point in enumerate(points):
        LOG.info('--------------------------------------------')
        LOG.info('--------------------------------------------')
        LOG.info(f'Step -> {i} / {len(points)}')
        LOG.info('--------------------------------------------')
        LOG.info(f'Moving to {point} from {inst.current_point}')
        inst.move_to_point(point)
        inst.scan()

        search(inst, point)

    dump(inst)


def _filter_no_items(inst: instance.Instance, points: List[utils.Point]):
    return list(filter(lambda p: len(inst.located[p[0]][p[1]]) != 0, points))


def search(inst: instance.Instance, point: utils.Point):
    # remove all that don't have any items
    points_with_items = _filter_no_items(inst, inst.all_points)
    anchor = utils.closest_point(points_with_items, point)

    # nothing around us has any trash so lets return
    if anchor is None:
        LOG.info(f'No items found around {point}')
        return

    LOG.info(f'Found {len(points_with_items)} points with items. Starting to search.')
    LOG.info(f'Using {anchor} as anchor point')
    point_within_radius = utils.points_around(anchor, inst.radius, inst.x_size, inst.y_size)
    point_within_radius = _filter_no_items(inst, point_within_radius)
    current_point = anchor
    while current_point is not None:
        LOG.info(f'Moving to {current_point}')
        inst.move_to_point(current_point)

        # Make a shallow copy of the list because collect will delete from located
        x, y = current_point
        for item_id in list(inst.located[x][y]):
            LOG.info(f'Collecting {item_id} in ({x}, {y})')
            inst.collect(x, y, item_id)

        point_within_radius = list(filter(lambda p: p != current_point, point_within_radius))
        current_point = utils.closest_point(point_within_radius, current_point)

    # move back to the anchor position
    LOG.info(f'Moving back to {anchor} and scanning')
    inst.move_to_point(anchor)
    inst.scan()

    LOG.info('Scanning again.')
    search(inst, anchor)


def dump(inst: instance.Instance):
    """
    Dump waste in the appropriate bin

    :param inst: instance of the current state
    """
    def unload(point: utils.Point, items: list):
        if len(items) == 0:
            return

        t = items[0]['type']
        LOG.info(f'Moving to the {t} bin at {point} to try and add {len(items)} items!')

        inst.move_to_point(point)
        # make sure to go in reverse since we will be deleting along the way
        for i, item in reversed(list(enumerate(items))):
            try:
                inst.unload(item, i)
                LOG.info(f'Added {t} item to bin.')
            except RuntimeFailure:
                LOG.info(f'{t} bin at capacity. Moving to the next location.')
                inst.move_to_point((point[0], point[1] - 1))
                # print(e)
                break

    while inst.held_garbage or inst.held_organic or inst.held_recycle:
        unload(inst.bin_location_organic, inst.held_organic)
        unload(inst.bin_location_recycle, inst.held_recycle)
        unload(inst.bin_location_garbage, inst.held_garbage)

    LOG.info('Finished dumping contents')
