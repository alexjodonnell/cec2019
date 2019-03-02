import backend
import instance
import utils

LOG = utils.get_logger(__file__)


def main():
    LOG.info('Starting service!')
    back = backend.Backend()
    try:
        LOG.info('Creating instance')
        inst = instance.Instance.from_backend(back)

    finally:
        LOG.info('Deleting instance')
        back.delete_instance()


if __name__ == '__main__':
    main()
