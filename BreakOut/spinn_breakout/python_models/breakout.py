# PACMAN imports
from pacman.executor.injection_decorator import inject_items
from pacman.model.decorators.overrides import overrides
from pacman.model.graphs.application.impl.application_vertex import \
    ApplicationVertex
from pacman.model.resources.cpu_cycles_per_tick_resource import \
    CPUCyclesPerTickResource
from pacman.model.resources.dtcm_resource import DTCMResource
from pacman.model.resources.resource_container import ResourceContainer
from pacman.model.resources.sdram_resource import SDRAMResource

# SpinnFrontEndCommon imports
from spinn_front_end_common.abstract_models\
    .abstract_binary_uses_simulation_run import AbstractBinaryUsesSimulationRun
from spinn_front_end_common.abstract_models \
    .abstract_generates_data_specification \
    import AbstractGeneratesDataSpecification
from spinn_front_end_common.abstract_models.abstract_has_associated_binary \
    import AbstractHasAssociatedBinary
from spinn_front_end_common.abstract_models.\
    abstract_provides_outgoing_partition_constraints import \
    AbstractProvidesOutgoingPartitionConstraints
from pacman.model.constraints.key_allocator_constraints\
    .key_allocator_contiguous_range_constraint \
    import KeyAllocatorContiguousRangeContraint
from spinn_front_end_common.interface.simulation import simulation_utilities
from spinn_front_end_common.utilities import constants as\
    front_end_common_constants

# sPyNNaker imports
from spynnaker.pyNN.models.common.population_settable_change_requires_mapping \
    import PopulationSettableChangeRequiresMapping
from spynnaker.pyNN.utilities import constants

# Breakout imports
from breakout_machine_vertex import BreakoutMachineVertex

# ----------------------------------------------------------------------------
# Breakout
# ----------------------------------------------------------------------------
# **HACK** for Projection to connect a synapse type is required
class BreakoutSynapseType(object):
    def get_synapse_id_by_target(self, target):
        return 0

# ----------------------------------------------------------------------------
# Breakout
# ----------------------------------------------------------------------------
class Breakout(
    ApplicationVertex, AbstractGeneratesDataSpecification,
    AbstractHasAssociatedBinary, AbstractProvidesOutgoingPartitionConstraints,
    PopulationSettableChangeRequiresMapping, AbstractBinaryUsesSimulationRun):

    BREAKOUT_REGION_BYTES = 4
    WIDTH_PIXELS = 160
    HEIGHT_PIXELS = 128
    COLOUR_BITS = 2

    # **HACK** for Projection to connect a synapse type is required
    synapse_type = BreakoutSynapseType()

    def __init__(self, n_neurons, constraints=None, label="Breakout"):
        # **NOTE** n_neurons currently ignored - width and height will be
        # specified as additional parameters, forcing their product to be
        # duplicated in n_neurons seems pointless
        
        # *** NOTE *** we use n_neurons to establish wether it's a production (1)
        # or a testing (2) scenario. A testing environment will reduce resolution
        # to a quarter.
        self.testing = True if n_neurons == 2 else False
        
        # Superclasses
        ApplicationVertex.__init__(
            self, label, constraints, self.n_atoms)
        AbstractProvidesOutgoingPartitionConstraints.__init__(self)
        PopulationSettableChangeRequiresMapping.__init__(self)

    def get_maximum_delay_supported_in_ms(self, machine_time_step):
        # Breakout has no synapses so can simulate only one time step of delay
        return machine_time_step / 1000.0

    # ------------------------------------------------------------------------
    # ApplicationVertex overrides
    # ------------------------------------------------------------------------
    @overrides(ApplicationVertex.get_resources_used_by_atoms)
    def get_resources_used_by_atoms(self, vertex_slice):
        # **HACK** only way to force no partitioning is to zero dtcm and cpu
        container = ResourceContainer(
            sdram=SDRAMResource(
                self.BREAKOUT_REGION_BYTES +
                front_end_common_constants.SYSTEM_BYTES_REQUIREMENT),
            dtcm=DTCMResource(0),
            cpu_cycles=CPUCyclesPerTickResource(0))

        return container


    @overrides(ApplicationVertex.create_machine_vertex)
    def create_machine_vertex(self, vertex_slice, resources_required,
                              label=None, constraints=None):
        # Return suitable machine vertex
        return BreakoutMachineVertex(resources_required, constraints, label)

    @property
    @overrides(ApplicationVertex.n_atoms)
    def n_atoms(self):
        # **TODO** should we calculate this automatically
        # based on log2 of width and height?
        return 2 +(256 * 256 * 2)
        # if self.testing:
            # return 2 + (64 * 32 * 2)
        # else:
            # return 2 + (256 * 128 * 2)

    # ------------------------------------------------------------------------
    # AbstractGeneratesDataSpecification overrides
    # ------------------------------------------------------------------------
    @inject_items({"machine_time_step": "MachineTimeStep",
                   "time_scale_factor": "TimeScaleFactor",
                   "graph_mapper": "MemoryGraphMapper",
                   "routing_info": "MemoryRoutingInfos",
                   "tags": "MemoryTags",
                   "n_machine_time_steps": "TotalMachineTimeSteps"})
    @overrides(AbstractGeneratesDataSpecification.generate_data_specification,
               additional_arguments={"machine_time_step", "time_scale_factor",
                                     "graph_mapper", "routing_info", "tags",
                                     "n_machine_time_steps"}
    )
    def generate_data_specification(self, spec, placement, machine_time_step,
                                    time_scale_factor, graph_mapper,
                                    routing_info, tags, n_machine_time_steps):
        vertex = placement.vertex
        vertex_slice = graph_mapper.get_slice(vertex)

        spec.comment("\n*** Spec for Breakout Instance ***\n\n")
        spec.comment("\nReserving memory space for data regions:\n\n")

        # Reserve memory:
        spec.reserve_memory_region(
            region=BreakoutMachineVertex._BREAKOUT_REGIONS.SYSTEM.value,
                    size=front_end_common_constants.SYSTEM_BYTES_REQUIREMENT,
                    label='setup')
        spec.reserve_memory_region(
            region=BreakoutMachineVertex._BREAKOUT_REGIONS.BREAKOUT.value,
                    size=self.BREAKOUT_REGION_BYTES, label='BreakoutParams')
        # vertex.reserve_provenance_data_region(spec)

        # Write setup region
        spec.comment("\nWriting setup region:\n")
        spec.switch_write_focus(
            BreakoutMachineVertex._BREAKOUT_REGIONS.SYSTEM.value)
        spec.write_array(simulation_utilities.get_simulation_header_array(
            self.get_binary_file_name(), machine_time_step,
            time_scale_factor))

        # Write breakout region containing routing key to transmit with
        spec.comment("\nWriting breakout region:\n")
        spec.switch_write_focus(
            BreakoutMachineVertex._BREAKOUT_REGIONS.BREAKOUT.value)
        spec.write_value(routing_info.get_first_key_from_pre_vertex(
            vertex, constants.SPIKE_PARTITION_ID))

        # End-of-Spec:
        spec.end_specification()

    # ------------------------------------------------------------------------
    # AbstractHasAssociatedBinary overrides
    # ------------------------------------------------------------------------
    @overrides(AbstractHasAssociatedBinary.get_binary_file_name)
    def get_binary_file_name(self):
        if self.testing:
            return "breakout_test.aplx"
        else:
            return "breakout.aplx"

    # ------------------------------------------------------------------------
    # AbstractProvidesOutgoingPartitionConstraints overrides
    # ------------------------------------------------------------------------
    @overrides(AbstractProvidesOutgoingPartitionConstraints.
               get_outgoing_partition_constraints)
    def get_outgoing_partition_constraints(self, partition):
        return [KeyAllocatorContiguousRangeContraint()]
