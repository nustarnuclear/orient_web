import os
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.db.models import Q
from .storage import NymphStorage, get_file_root


# Create your models here.
def custom_path(instance, filename):
    base = instance.dir()
    return os.path.join(base, filename)


class BaseModel(models.Model):
    remark = models.TextField(blank=True)
    time_inserted = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def dir(self, ):
        return get_file_root()

    def chdir(self):
        dir = self.dir()
        os.chdir(dir)

    def __str__(self):
        return "{}({}): ".format(self.pk, self.remark)


class Profile(models.Model):
    user = models.OneToOneField(User)
    plants = models.ManyToManyField("Plant")

    def dir(self, plant_id):
        plant_dir = self.plants.get(id=plant_id).dir()
        return os.path.join(plant_dir, "user_" + str(self.user.id))

    class Meta:
        db_table = "profile"


class GenericModel(models.Model):
    content_type = models.ForeignKey(ContentType,editable=False, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField(editable=False)
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        abstract = True

    def __str__(self):
        return str(self.content_object)


########################################################################################################################
# nucliede,element,material
########################################################################################################################
# describe element information
class Element(models.Model):
    atomic_num = models.PositiveSmallIntegerField(primary_key=True, verbose_name='Atomic number')
    symbol = models.CharField(max_length=8, unique=True)
    nameCH = models.CharField(max_length=8, verbose_name='Chinese name')
    nameEN = models.CharField(max_length=40, verbose_name='English name')

    class Meta:
        db_table = 'element'
        ordering = ['atomic_num']

    def __str__(self):
        return self.symbol


class WimsNuclide(models.Model):
    NF_CHOICES = (
        (0, '无共振积分表'),
        (1, '有共振积分表的非裂变核'),
        (2, '有共振吸收共振积分表的可裂变核'),
        (3, '有共振吸收和共振裂变共振积分表的可裂变核'),
        (4, '没有共振积分表的可裂变核'),
    )
    MATERIAL_TYPE_CHOICES = (
        ('M', '慢化剂'),
        ('FP', '裂变产物'),
        ('A', '锕系核素'),
        ('B', '可燃核素'),
        ('D', '用于剂量的材料'),
        ('S', '结构材料和其他'),
        ('B/FP', '可燃核素 /裂变产物'),
    )
    element = models.ForeignKey(Element, blank=True, null=True)
    nuclide_name = models.CharField(max_length=30, )
    id_wims = models.PositiveIntegerField(unique=True, blank=True, null=True)
    id_self_defined = models.PositiveIntegerField(unique=True, blank=True, null=True)
    amu = models.DecimalField(max_digits=9, decimal_places=6, validators=[MinValueValidator(0), ])
    nf = models.PositiveSmallIntegerField(choices=NF_CHOICES)
    material_type = models.CharField(max_length=4, choices=MATERIAL_TYPE_CHOICES)
    description = models.CharField(max_length=50)

    class Meta:
        db_table = 'wims_nuclide'

    @property
    def res_trig(self):
        return 0 if self.nf in (0, 4) else 1

    @property
    def dep_trig(self):
        return 1 if self.material_type in ('FP', 'A', 'B', 'B/FP') else 0

    @classmethod
    def generate_nuclide_lib(cls):
        data = cls.objects.exclude(material_type='D')
        for item in data:
            id_wims = item.id_wims if item.id_wims else 0
            yield (item.id_self_defined, id_wims, item.amu, item.res_trig, item.dep_trig)

    def __str__(self):
        return "{}".format(self.nuclide_name)


class WmisElement(models.Model):
    name = models.CharField(max_length=30, )
    wmis_nuclides = models.ManyToManyField(WimsNuclide, through='WmisElementComposition')

    class Meta:
        db_table = 'wmis_element'
        ordering = ['name']

    def get_nuclide_num(self):
        return self.wmis_nuclides.count()

    def __str__(self):
        return self.name


class WmisElementComposition(models.Model):
    wmis_element = models.ForeignKey(WmisElement, related_name='composition')
    wmis_nuclide = models.ForeignKey(WimsNuclide)
    weight_percent = models.DecimalField(max_digits=9, decimal_places=6,
                                         validators=[MaxValueValidator(100), MinValueValidator(0)], help_text=r"unit:%")

    class Meta:
        db_table = 'wmis_element_composition'

    def __str__(self):
        return '{} {}'.format(self.wmis_element, self.wmis_nuclide)


class BasicMaterial(BaseModel):
    TYPE_CHOICES = (
        (1, 'by number'),
        (2, 'by weight percent'),
    )
    name = models.CharField(max_length=16, unique=True)
    density = models.DecimalField(max_digits=10, decimal_places=5, help_text=r'unit:g/cm3')
    input_type = models.PositiveSmallIntegerField(default=1, choices=TYPE_CHOICES)

    class Meta:
        db_table = 'basic_material'

    def __str__(self):
        return self.name


class BasicMaterialNumCompo(models.Model):
    basic_material = models.ForeignKey(BasicMaterial, related_name='num_compo')
    element = models.ForeignKey(WmisElement, )
    element_number = models.PositiveSmallIntegerField()

    class Meta:
        db_table = 'basic_material_num_compo'
        order_with_respect_to = 'basic_material'


class BasicMaterialWgtCompo(models.Model):
    basic_material = models.ForeignKey(BasicMaterial, related_name='wgt_compo')
    element = models.ForeignKey(WmisElement, )
    weight_percent = models.DecimalField(max_digits=10, decimal_places=5,
                                         validators=[MaxValueValidator(100), MinValueValidator(0)], help_text=r"%", )

    class Meta:
        db_table = 'basic_material_wgt_compo'
        order_with_respect_to = 'basic_material'


class Mixture(BaseModel):
    TYPE_CHOICES = (
        (1, 'by weight'),
        (2, 'by volume'),
    )
    name = models.CharField(max_length=16, unique=True)
    basic_materials = models.ManyToManyField(BasicMaterial, through='MixtureCompo')
    input_type = models.PositiveSmallIntegerField(default=1, choices=TYPE_CHOICES)

    class Meta:
        db_table = 'mixture'

    def __str__(self):
        return self.name


class MixtureCompo(models.Model):
    mixture = models.ForeignKey(Mixture, related_name='compo', )
    basic_material = models.ForeignKey(BasicMaterial)
    percent = models.DecimalField(max_digits=10, decimal_places=5,
                                  validators=[MaxValueValidator(100), MinValueValidator(0)], help_text=r"unit:%")

    class Meta:
        db_table = 'mixture_compo'


class SymbolicMaterial(BaseModel):
    """
    FUEL means the common UO2 fuel;
    MOD means the H2O moderator
    """
    NAME_CHOICES = (
        ("FUEL", "Common UO2 fuel"),
        ("MOD", "H2O moderator")
    )
    name = models.CharField(max_length=8, unique=True, choices=NAME_CHOICES)

    class Meta:
        db_table = 'symbolic_material'

    def __str__(self):
        return self.name


class Material(GenericModel):
    class Meta:
        db_table = "material"


class Fuel(models.Model):
    material = models.ForeignKey(Material)
    density = models.DecimalField(max_digits=10, decimal_places=5, help_text=r'unit:g/cm3')
    enrichment = models.DecimalField(max_digits=10, decimal_places=5,
                                     validators=[MaxValueValidator(100), MinValueValidator(0)],
                                     help_text=r"%")

    class Meta:
        db_table = "fuel"


########################################################################################################################
# to describe rod
########################################################################################################################
class RodIntersectSurface(BaseModel):
    """
    to describe rod that has not axial lamination
    """
    outer_diameter = models.DecimalField(max_digits=10, decimal_places=5, validators=[MinValueValidator(0)],
                                         help_text='unit:cm')
    inner_diameter = models.DecimalField(max_digits=10, decimal_places=5, validators=[MinValueValidator(0)],
                                         help_text='unit:cm', default=0)
    materials = models.ManyToManyField(Material, through="RodIntersectSurfaceMaterial")

    class Meta:
        db_table = "rod_intersect_surface"


class RodIntersectSurfaceMaterial(models.Model):
    intersect_surface = models.ForeignKey(RodIntersectSurface)
    material = models.ForeignKey(Material)
    outer_diameter = models.DecimalField(max_digits=10, decimal_places=5, validators=[MinValueValidator(0)],
                                         help_text='unit:cm', default=0)

    class Meta:
        db_table = "rod_intersect_surface_material"
        order_with_respect_to = 'intersect_surface'


class Rod(BaseModel):
    USAGE_CHOICES = (
        (1, "Fuel element WITH OUT SPECIFIC FUEL"),
        (2, "control rod"),
        (3, "burnable poison rod"),
        (4, "guide tube"),
        (5, "instrument tube"),
    )
    usage = models.PositiveSmallIntegerField(choices=USAGE_CHOICES)
    intersect_surfaces = models.ManyToManyField(RodIntersectSurface, through="RodCut")

    class Meta:
        db_table = "rod"


class RodCut(models.Model):
    rod = models.ForeignKey(Rod)
    intersect_surface = models.ForeignKey(RodIntersectSurface)
    length = models.DecimalField(max_digits=10, decimal_places=5, validators=[MinValueValidator(0), ],
                                 help_text=r"unit:cm")

    class Meta:
        db_table = "rod_cut"
        order_with_respect_to = 'rod'


class AssemblyIntersectSurface(models.Model):
    """
    map is like 1:2,2,4,5\n2:3,3,3,
    while 1 mean the line number; 2,2,4,5 means the intersect surface pk
    fuel means if cut surface is fuel map
    """

    rod_intersect_surfaces = models.ManyToManyField(RodIntersectSurface, through="AssemblyIntersectSurfaceCompo")
    fuel = models.BooleanField()
    position_pattern = models.ForeignKey("PositionPattern")

    class Meta:
        db_table = "assembly_intersect_surface"


class AssemblyIntersectSurfaceCompo(models.Model):
    assembly_intersect_surface = models.ForeignKey(AssemblyIntersectSurface)
    rod_intersect_surface = models.ForeignKey(RodIntersectSurface)
    position = models.ForeignKey("AssemblyPosition")

    class Meta:
        db_table = "assembly_intersect_surface_compo"


class AssemblyCut(GenericModel):
    """
    object point to models which define a generic relation to itself

    """

    intersect_surface = models.ForeignKey(AssemblyIntersectSurface)
    distance = models.DecimalField(max_digits=10, decimal_places=5, default=0, validators=[MinValueValidator(0)],
                                   help_text=r"cm from intersect surface to fuel active top")

    class Meta:
        db_table = "assembly_cut"


########################################################################################################################
# to describe position
########################################################################################################################
class Coordinate(models.Model):
    row = models.PositiveSmallIntegerField()
    column = models.PositiveSmallIntegerField()

    class Meta:
        unique_together = ("row", "column")
        db_table = "coordinate"

    def __str__(self):
        return "R{}C{}".format(self.row, self.column)


class AbstractPosition(models.Model):
    coordinates = models.ManyToManyField(Coordinate)

    class Meta:
        abstract = True


class PositionPattern(BaseModel):
    TYPE_CHOICES = (
        (1, "ASSEMBLY"),
        (2, "CORE"),

    )
    name = models.CharField(max_length=32, unique=True)
    type = models.PositiveSmallIntegerField(choices=TYPE_CHOICES)

    class Meta:
        db_table = 'position_pattern'

    def __str__(self):
        return self.name


class AssemblyPosition(AbstractPosition):
    TYPE_CHOICES = (
        (1, "FUEL"),
        (2, "GUIDE TUBE"),
        (3, "INSTRUMENT TUBE"),
    )
    pattern = models.ForeignKey(PositionPattern, limit_choices_to={"type": 1})
    type = models.PositiveSmallIntegerField(choices=TYPE_CHOICES, default=1)

    class Meta:
        db_table = 'assembly_position'


class ReactorPosition(AbstractPosition):
    pattern = models.ForeignKey(PositionPattern, limit_choices_to={"type": 2})

    class Meta:
        db_table = 'reactor_position'


########################################################################################################################
# to describe fuel component
########################################################################################################################

########################################################################################################################
# to describe FUEL PELLET
########################################################################################################################
class FuelPelletModel(GenericModel):
    diameter = models.DecimalField(max_digits=10, decimal_places=5, validators=[MinValueValidator(0)],
                                   help_text='unit:cm', default=0)
    volume_percent = models.DecimalField(max_digits=10, decimal_places=5,
                                         validators=[MaxValueValidator(100), MinValueValidator(0)], help_text=r"unit:%")
    density_percent = models.DecimalField(max_digits=10, decimal_places=5, default=95,
                                          validators=[MaxValueValidator(100), MinValueValidator(0)],
                                          help_text=r"%")

    coated_material = models.ForeignKey(Material, blank=True, null=True)
    coated_thickness = models.DecimalField(max_digits=10, decimal_places=5, validators=[MinValueValidator(0)],
                                           help_text='unit:cm', default=0)
    linear_density = models.DecimalField(max_digits=10, decimal_places=5, blank=True, null=True, help_text=r'B10 mg/cm')

    class Meta:
        db_table = "fuel_pellet_model"


class FuelPelletType(BaseModel):
    model = models.ForeignKey(FuelPelletModel)
    fuel = models.ForeignKey(Fuel)

    class Meta:
        db_table = "fuel_pellet_type"


########################################################################################################################
# to describe FUEL ELEMENT
########################################################################################################################
class FuelElementType(BaseModel):
    """
    actually insert fuel inside the fuel element
    """
    rod = models.ForeignKey(Rod, limit_choices_to={"usage": 1})
    pellets = models.ManyToManyField(FuelPelletType, through="PelletLoadingPattern")

    class Meta:
        db_table = "fuel_element_type"


class PelletLoadingPattern(models.Model):
    fuel_element_type = models.ForeignKey(FuelElementType)
    fuel_pellet_type = models.ForeignKey(FuelPelletType)
    height = models.DecimalField(max_digits=10, decimal_places=5, validators=[MinValueValidator(0), ],
                                 help_text=r"unit:cm Based on bottom")

    class Meta:
        db_table = "pellet_loading_pattern"
        order_with_respect_to = "fuel_element_type"


########################################################################################################################
# to describe FUEL ASSEMBLY
########################################################################################################################
class AbstractAssembly(BaseModel):
    name = models.CharField(max_length=16)
    position_pattern = models.ForeignKey(PositionPattern, limit_choices_to={"type": 1})
    cuts = GenericRelation(AssemblyCut)
    symmetry = models.BooleanField(default=True, help_text=r"satisfy 1/8 symmetry")

    class Meta:
        abstract = True


class Grid(BaseModel):
    volume = models.DecimalField(max_digits=10, decimal_places=5, validators=[MinValueValidator(0)], help_text='cm3')
    height = models.DecimalField(max_digits=10, decimal_places=5, validators=[MinValueValidator(0)], help_text='cm')
    material = models.ForeignKey(Material)

    class Meta:
        db_table = "grid"


class FuelAssemblyModel(AbstractAssembly):
    """
    cuts: pin map: without fuel inside but includes bpa
    """
    active_length = models.DecimalField(max_digits=10, decimal_places=5, validators=[MinValueValidator(0)],
                                        help_text=r'unit:cm')
    side_length = models.DecimalField(max_digits=10, decimal_places=5, validators=[MinValueValidator(0)],
                                      help_text=r'unit:cm')
    guide_tube = models.ForeignKey(Rod, limit_choices_to={"usage": 4}, related_name="fuel_assembly_models")
    instrument_tube = models.ForeignKey(Rod, limit_choices_to={"usage": 4}, blank=True, null=True)
    pin_pitch = models.DecimalField(max_digits=10, decimal_places=5, validators=[MinValueValidator(0)],
                                    help_text=r'unit:cm')
    grids = models.ManyToManyField(Grid, through="GridLoadingPattern")

    class Meta:
        db_table = "fuel_assembly_model"


class GridLoadingPattern(models.Model):
    fuel_assembly_model = models.ForeignKey(FuelAssemblyModel)
    height = models.DecimalField(max_digits=10, decimal_places=5, validators=[MinValueValidator(0)],
                                 help_text=r'unit:cm')
    grid = models.ForeignKey(Grid)

    class Meta:
        db_table = "grid_loading_pattern"
        order_with_respect_to = "fuel_assembly_model"


class FuelAssemblyType(models.Model):
    model = models.ForeignKey(FuelAssemblyModel)
    fuel_element_types = models.ManyToManyField(FuelElementType, through="FuelElementLoadingPattern")
    assembly_enrichment = models.DecimalField(max_digits=9, decimal_places=6, validators=[MinValueValidator(0)], )
    cuts = GenericRelation(AssemblyCut, help_text="only consider fuel(IFBA,GD)")

    class Meta:
        db_table = "fuel_assembly_type"


class FuelElementLoadingPattern(models.Model):
    fuel_assembly_type = models.ForeignKey(FuelAssemblyType)
    fuel_element_type = models.ForeignKey(FuelElementType)
    position = models.ForeignKey(AssemblyPosition, limit_choices_to={"type": 1})

    class Meta:
        db_table = "fuel_element_loading_pattern"


class FuelAssembly(BaseModel):
    fuel_assembly_type = models.ForeignKey(FuelAssemblyType)
    product_num = models.CharField(max_length=32, blank=True, null=True)

    class Meta:
        db_table = 'fuel_assembly'


########################################################################################################################
# to describe COMPONENT ASSEMBLY
########################################################################################################################
class ComponentAssembly(AbstractAssembly):
    """
    cuts: pin map
    """
    TYPE_CHOICES = (
        (1, "control rod assembly"),
        (2, "burnable poison assembly")
    )
    component_rods = models.ManyToManyField(Rod, through="ComponentRodLoadingPattern")
    type = models.PositiveSmallIntegerField(choices=TYPE_CHOICES)

    class Meta:
        db_table = 'component_rod_assembly'


class ComponentRodLoadingPattern(models.Model):
    component_assembly = models.ForeignKey(ComponentAssembly)
    component_rod = models.ForeignKey(Rod, limit_choices_to=Q(usage__in=[2, 3]))
    position = models.ForeignKey(AssemblyPosition, limit_choices_to={"type": 2})
    gap = models.DecimalField(max_digits=10, decimal_places=5, default=0, validators=[MinValueValidator(0)],
                              help_text=r"cm gap from absorb top to component assembly base")

    class Meta:
        db_table = 'component_rod_loading_pattern'


class ControlRodCluster(BaseModel):
    reactor_model = models.ForeignKey("ReactorModel")
    cluster_name = models.CharField(max_length=5)
    component_assembly = models.ForeignKey(ComponentAssembly, limit_choices_to={"type": 1})

    class Meta:
        db_table = 'control_rod_cluster'


########################################################################################################################
# reactor information
########################################################################################################################
class ReactorModel(BaseModel):
    DIRECTION_CHOICES = (
        ('E', 'East'),
        ('S', 'South'),
        ('W', 'West'),
        ('N', 'North'),
    )
    NAME_CHOICES = (
        ("AP1000", "AP1000"),
        ("M310", "M310"),
        ("CP600", "CP600"),
        ("CP300", "CP300"),
        ("MINI_CORE", "MINI_CORE"),
    )
    name = models.CharField(max_length=12, choices=NAME_CHOICES)
    position_pattern = models.ForeignKey(PositionPattern, limit_choices_to={"type": 2})
    row_index = models.CharField(max_length=32, help_text='separated by blank space')
    column_index = models.CharField(max_length=32, help_text='separated by blank space')
    assembly_pitch = models.DecimalField(max_digits=10, decimal_places=5, validators=[MinValueValidator(0)],
                                         help_text='unit:cm', null=True)
    diameter = models.DecimalField(max_digits=10, decimal_places=5, validators=[MinValueValidator(0)],
                                   help_text='cm core_equivalent_diameter')
    active_height = models.DecimalField(max_digits=10, decimal_places=5, validators=[MinValueValidator(0)],
                                        help_text='unit:cm')
    primary_system_pressure = models.DecimalField(max_digits=10, decimal_places=5, validators=[MinValueValidator(0)],
                                                  help_text='unit:MPa')
    rated_power = models.DecimalField(max_digits=10, decimal_places=5, validators=[MinValueValidator(0)],
                                      help_text=r'MW thermal power')
    power_density = models.DecimalField(max_digits=10, decimal_places=5, validators=[MinValueValidator(0)],
                                        help_text=r'unit:W/g (fuel)')
    coolant_volume = models.DecimalField(max_digits=10, decimal_places=5, validators=[MinValueValidator(0)],
                                         help_text=r'unit:10e6m3', )
    coolant_flow_rate = models.DecimalField(max_digits=10, decimal_places=5, validators=[MinValueValidator(0)],
                                            help_text=r'unit:m3/h')
    fuel_temperature = models.PositiveSmallIntegerField(help_text='K')
    moderator_temperature = models.PositiveSmallIntegerField(help_text='K')
    step_size = models.DecimalField(max_digits=10, decimal_places=5, validators=[MinValueValidator(0)],
                                    help_text='unit:cm control rod', )
    default_step = models.PositiveSmallIntegerField(help_text='control rod', )
    max_step = models.PositiveSmallIntegerField(help_text='control rod', )
    set_zero_to_direction = models.CharField(max_length=1, choices=DIRECTION_CHOICES, default='E')
    clockwise_increase = models.BooleanField(default=True)

    def dir(self, ):
        base = super().dir()
        return os.path.join(base, self.name)

    class Meta:
        db_table = 'reactor_model'


class AbstractBaffle(models.Model):
    reactor_model = models.OneToOneField(ReactorModel)
    gap_to_fuel = models.DecimalField(max_digits=10, decimal_places=5, validators=[MinValueValidator(0)],
                                      help_text='unit:cm')
    material = models.ForeignKey(Material)
    thickness = models.DecimalField(max_digits=10, decimal_places=5, validators=[MinValueValidator(0)],
                                    help_text='unit:cm')

    class Meta:
        abstract = True


class RadialBaffle(AbstractBaffle):
    outer_diameter = models.DecimalField(max_digits=10, decimal_places=5, validators=[MinValueValidator(0)],
                                         help_text='unit:cm', blank=True, null=True)

    class Meta:
        db_table = 'radial_baffle'


class BottomBaffle(AbstractBaffle):
    class Meta:
        db_table = 'bottom_baffle'


class TopBaffle(AbstractBaffle):
    class Meta:
        db_table = 'top_baffle'


class ControlRodClusterLoadingPattern(models.Model):
    reactor_model = models.ForeignKey(ReactorModel)
    control_rod_cluster = models.ForeignKey(ControlRodCluster)
    position = models.ForeignKey(ReactorPosition)

    class Meta:
        db_table = 'control_rod_cluster_loading_pattern'


########################################################################################################################
# plant information
########################################################################################################################
class Plant(BaseModel):
    name = models.CharField(max_length=32)

    class Meta:
        db_table = 'plant'

    def dir(self):
        base = super().dir()
        return os.path.join(base, "plant_" + str(self.pk))

    def __str__(self):
        return super().__str__() + self.name


class Unit(BaseModel):
    plant = models.ForeignKey(Plant)
    unit_num = models.PositiveSmallIntegerField()
    reactor_model = models.ForeignKey(ReactorModel)

    def dir(self, user_id):
        user = User.objects.get(id=id)
        user_dir = user.profile.dir(self.plant_id)
        return os.path.join(user_dir, "unit_" + str(self.unit_num))

    class Meta:
        db_table = 'unit'
        order_with_respect_to = "plant"


########################################################################################################################
# Operation information
########################################################################################################################
class Cycle(BaseModel):
    unit = models.ForeignKey(Unit)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    cycle_num = models.PositiveSmallIntegerField()
    pull_outs = models.ManyToManyField(ControlRodClusterLoadingPattern,
                                       help_text=r"to pull out the control rod cluster at specific position")

    def dir(self, user_id):
        unit_dir = self.unit.dir(user_id)
        return os.path.join(unit_dir, "cycle_" + str(self.cycle_num))

    class Meta:
        db_table = 'cycle'
        order_with_respect_to = "unit"


class AbnormalAssembly(BaseModel):
    SITUATION_CHOICES = (
        (1, "broken but still available"),
        (2, "unavailable"),
    )
    fuel_assembly = models.ForeignKey(FuelAssembly)
    cycle = models.ForeignKey(Cycle, help_text="broken at which cycle or unavailable since which cycle(not include)")
    situation = models.PositiveSmallIntegerField(choices=SITUATION_CHOICES)

    class Meta:
        db_table = "abnormal_assembly"


class FuelAssemblyLoadingPattern(models.Model):
    cycle = models.ForeignKey(Cycle)
    fuel_assembly = models.ForeignKey(FuelAssembly)
    burnable_poison_assembly = models.ForeignKey(ComponentAssembly, blank=True, null=True, limit_choices_to={"type": 2})
    gap = models.DecimalField(max_digits=10, decimal_places=5, default=0, validators=[MinValueValidator(0)],
                              help_text=r"cm gap from component assembly base to fuel active top")
    position = models.ForeignKey(ReactorPosition)

    class Meta:
        db_table = 'fuel_assembly_loading_pattern'


########################################################################################################################
# calculation
########################################################################################################################
class ComputeNode(models.Model):
    name = models.CharField(max_length=32, unique=True)
    IP = models.GenericIPAddressField(unique=True)
    queue = models.CharField(max_length=32, unique=True)

    class Meta:
        db_table = "compute_node"


class AbstractTask(BaseModel):
    """
    prepared: task generated already but not sent to RabbitMQ
    waiting: sent to RabbitMQ but not consumed by compute server
    calculating: already under calculation
    suspended: pause by command but can restart again
    canceled: cancel the task when waiting
    stopped: stop the task when calculating
    completed: complete normally
    error: failed by a error
    """
    STATUS_CHOICES = (
        (0, 'prepared'),
        (1, 'waiting'),
        (2, 'calculating'),
        (3, 'suspended'),
        (4, 'canceled'),
        (5, 'stopped'),
        (6, 'completed'),
        (7, 'error'),
    )

    name = models.CharField(max_length=32)
    user = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL)
    status = models.PositiveSmallIntegerField(default=0, choices=STATUS_CHOICES)
    start_time = models.DateTimeField(blank=True, null=True)
    end_time = models.DateTimeField(blank=True, null=True)
    compute_node = models.ForeignKey(ComputeNode, blank=True, null=True)

    # input_file = models.FileField(upload_to=task_path, storage=NymphStorage(), blank=True, null=True)
    # authorized = models.BooleanField(default=False)

    @property
    def time_cost(self):
        return self.end_time - self.start_time

    class Meta:
        abstract = True


class AssemblyCalculation(BaseModel):
    reactor_model = models.ForeignKey(ReactorModel)
    fuel_assembly_type = models.ForeignKey(FuelAssemblyType)
    burnable_poison_assembly = models.ForeignKey(ComponentAssembly, limit_choices_to={"type": 2}, blank=True, null=True)
    gap = models.DecimalField(max_digits=10, decimal_places=5, default=0, validators=[MinValueValidator(0)],
                              help_text=r"cm gap from component assembly base to fuel active top")
    cuts = GenericRelation(AssemblyCut)

    class Meta:
        db_table = "assembly_calculation"


DEP_STRATEGY_CHOICES = (
    ('LLR', 'LLR'),
    ('PPC', 'PPC'),
    ('LR', 'LR'),
    ('PC', 'PC'),
)

POLAR_TYPE_CHOICES = (
    ('LCMD', 'LCMD'),
    ('TYPL', 'TYPL'),
    ('DeCT', 'DeCT'),
)

LEAKAGE_PATH_CHOICES = (
    (0, 0),
    (1, 1),
    (2, 2),
)
LEAKAGE_METHOD_CHOICES = (
    ('B1', 'B1'),
    ('P1', 'P1'),
)
CONDENSATION_PATH_CHOICES = (
    (0, 0),
    (1, 1),
    (2, 2),
)
NUM_GROUP_2D_CHOICES = (
    (2, 2),
    (3, 3),
    (4, 4),
    (8, 8),
    (18, 18),
    (25, 25),
    (33, 33),
)


class AssemblyTask(AbstractTask):
    """
    one layer for assembly
    prepare for pre robin input
    """
    reactor_model = models.ForeignKey(ReactorModel)
    pin_map = models.ForeignKey(AssemblyIntersectSurface, limit_choices_to={"fuel": False},
                                related_name="pre_robin_tasks")
    fuel_map = models.ForeignKey(AssemblyIntersectSurface, limit_choices_to={"fuel": True})
    bp_in = models.BooleanField(help_text="if bp rod in")
    ####################################################################################################################
    # branch info
    max_burn_up_point = models.DecimalField(max_digits=10, decimal_places=5, validators=[MinValueValidator(0)],
                                            default=65, help_text='GWd/tU')
    max_boron_density = models.PositiveSmallIntegerField(default=2000, help_text='ppm')
    min_boron_density = models.PositiveSmallIntegerField(default=0, help_text='ppm')
    boron_density_interval = models.PositiveSmallIntegerField(help_text='ppm', default=200)
    # fuel temperature branch
    max_fuel_temperature = models.PositiveSmallIntegerField(help_text='K', default=1253)
    min_fuel_temperature = models.PositiveSmallIntegerField(help_text='K', default=553)
    fuel_temperature_interval = models.PositiveSmallIntegerField(help_text='K', default=50, )
    # moderator temperature branch
    max_moderator_temperature = models.PositiveSmallIntegerField(help_text='K', default=615)
    min_moderator_temperature = models.PositiveSmallIntegerField(help_text='K', default=561)
    moderator_temperature_interval = models.PositiveSmallIntegerField(help_text='K', default=4)
    ####################################################################################################################
    # depletion state
    boron_density = models.PositiveSmallIntegerField(default=800, help_text='ppm')
    dep_strategy = models.CharField(max_length=3, choices=DEP_STRATEGY_CHOICES, default='LLR')
    ####################################################################################################################
    # model parameter
    # accuracy_control
    track_density = models.DecimalField(max_digits=5, decimal_places=5, default=0.03, validators=[MinValueValidator(0)],
                                        help_text='cm')
    polar_type = models.CharField(max_length=4, choices=POLAR_TYPE_CHOICES, default='LCMD')
    polar_azimuth = models.CommaSeparatedIntegerField(max_length=50, default='4,16')
    iter_inner = models.PositiveSmallIntegerField(default=3)
    iter_outer = models.PositiveSmallIntegerField(default=100)
    eps_keff = models.DecimalField(max_digits=7, decimal_places=7, validators=[MinValueValidator(0)], default=1e-5)
    eps_flux = models.DecimalField(max_digits=7, decimal_places=7, validators=[MinValueValidator(0)], default=1e-4)
    # fundamental_mode
    leakage_corrector_path = models.PositiveSmallIntegerField(choices=LEAKAGE_PATH_CHOICES, default=2)
    leakage_corrector_method = models.CharField(max_length=2, choices=LEAKAGE_METHOD_CHOICES, default='B1')
    buckling_or_keff = models.DecimalField(max_digits=10, decimal_places=5, default=1)
    # energy_condensation
    condensation_path = models.PositiveSmallIntegerField(choices=CONDENSATION_PATH_CHOICES, default=1)
    num_group_2D = models.PositiveSmallIntegerField(choices=NUM_GROUP_2D_CHOICES, default=25)
    # edit_control
    num_group_edit = models.PositiveSmallIntegerField(choices=NUM_GROUP_2D_CHOICES, default=2)
    micro_xs_output = models.BooleanField(default=False)

    robin_tasks = GenericRelation("RobinTask")

    def dir(self):
        reactor_model_dir = self.reactor_model.dir()
        return os.path.join(reactor_model_dir, "assembly_task", "task_" + str(self.pk))

    class Meta:
        db_table = "assembly_task"


class BPOutTask(AssemblyTask):
    burn_up_points = models.CharField(max_length=128)
    robin_tasks = GenericRelation("RobinTask")

    def dir(self,burn_up_point):
        base = super().dir()
        return os.path.join(base, "bp_out_task", "burn_up_" + str(burn_up_point))

    class Meta:
        db_table = "bp_out_task"


class BaffleCalculation(AbstractTask):
    assembly_task = models.OneToOneField(AssemblyTask)
    # accuracy_control
    track_density = models.DecimalField(max_digits=5, decimal_places=5, default=0.02, validators=[MinValueValidator(0)],
                                        help_text='cm')
    polar_type = models.CharField(max_length=4, choices=POLAR_TYPE_CHOICES, default='LCMD')
    polar_azimuth = models.CommaSeparatedIntegerField(max_length=50, default='4,4')
    iter_inner = models.PositiveSmallIntegerField(default=3)
    iter_outer = models.PositiveSmallIntegerField(default=100)
    eps_keff = models.DecimalField(max_digits=7, decimal_places=7, validators=[MinValueValidator(0)], default=1e-4)
    eps_flux = models.DecimalField(max_digits=7, decimal_places=7, validators=[MinValueValidator(0)], default=1e-4)
    # fundamental_mode
    leakage_corrector_path = models.PositiveSmallIntegerField(choices=LEAKAGE_PATH_CHOICES, default=0)
    leakage_corrector_method = models.CharField(max_length=2, choices=LEAKAGE_METHOD_CHOICES, default='B1')
    buckling_or_keff = models.DecimalField(max_digits=10, decimal_places=5, default=1)
    # energy_condensation
    condensation_path = models.PositiveSmallIntegerField(choices=CONDENSATION_PATH_CHOICES, default=2)
    num_group_2D = models.PositiveSmallIntegerField(choices=NUM_GROUP_2D_CHOICES, default=25)
    # edit_control
    num_group_edit = models.PositiveSmallIntegerField(choices=NUM_GROUP_2D_CHOICES, default=2)
    micro_xs_output = models.BooleanField(default=False)
    robin_tasks = GenericRelation("RobinTask")

    MODEL_TYPES = ['BR1', 'BR2', 'BR3', 'BR_BOT', 'BR_TOP']

    def dir(self, model_type):
        base = self.assembly_task.dir()
        return os.path.join(base, "baffle_task", model_type)

    class Meta:
        db_table = "baffle_calculation"


class RobinTask(AbstractTask, GenericModel):
    input_file = models.FileField(upload_to=custom_path, storage=NymphStorage())

    @property
    def reactor_model(self):
        return self.content_object.reactor_model

    def dir(self):
        return os.path.join(self.reactor_model.name, "robin_task", "task_" + self.id)

    class Meta:
        db_table = "robin_task"


class IdyllTask:
    """
    a non model class which will not create table in database
    task can be AssemblyTask,BPOutTask,BaffleCalculation
    """

    def __init__(self, task):
        self.task = task


class LoadingPattern(BaseModel):
    name = models.CharField(max_length=32)
    user = models.ForeignKey(User)
    pre_loading_pattern = models.ForeignKey('self', related_name='post_loading_patterns', blank=True, null=True)
    cycle = models.ForeignKey(Cycle)
    file = models.FileField(upload_to=custom_path)
    authorized = models.BooleanField(default=False)

    class Meta:
        db_table = "loading_pattern"

    def dir(self):
        user_id = self.user.id
        cycle_dir = self.cycle.dir(user_id)
        return os.path.join(cycle_dir, "loading_pattern", "pattern_" + str(self.id))


class ControlRodClusterMap(BaseModel):
    reactor_model = models.ForeignKey(ReactorModel)
    control_rod_clusters = models.ManyToManyField(ControlRodCluster, through="ControlRodClusterStep")

    class Meta:
        db_table = "control_rod_cluster_map"


class ControlRodClusterStep(models.Model):
    """
    a map to describe the control rod cluster step information
    """
    map = models.ForeignKey(ControlRodClusterMap)
    control_rod_cluster = models.ForeignKey(ControlRodCluster)
    step = models.DecimalField(max_digits=10, decimal_places=5, validators=[MinValueValidator(0)])

    class Meta:
        db_table = "control_rod_cluster_step"
        unique_together = ("map","control_rod_cluster")

class EgretTask(AbstractTask):
    loading_pattern = models.ForeignKey(LoadingPattern)
    input_file = models.FileField(upload_to=custom_path,storage=NymphStorage(),blank=True, null=True,)
    pre_egret_task = models.ForeignKey('self', related_name='post_egret_tasks', blank=True, null=True)
    authorized = models.BooleanField(default=False)

    class Meta:
        abstract = True

    def dir(self):
        user_id = self.user.id
        cycle_dir = self.cycle.dir(user_id)
        return os.path.join(cycle_dir, "egret_task", "task_" + str(self.id))

    @property
    def cycle(self):
        return self.loading_pattern.cycle


class EgretFollowTask(EgretTask):
    class Meta:
        db_table = "egret_follow_task"


class EgretFollowCase(models.Model):
    follow_task = models.ForeignKey(EgretFollowTask)
    burn_up = models.DecimalField(max_digits=10, decimal_places=5, validators=[MinValueValidator(0)],
                                  help_text='unit:MWd/tU', blank=True, null=True)
    delta_time = models.DecimalField(max_digits=10, decimal_places=5, validators=[MinValueValidator(0)],
                                     help_text='unit:day', blank=True, null=True)
    relative_power = models.DecimalField(max_digits=5, decimal_places=4,
                                         validators=[MinValueValidator(0), MaxValueValidator(1)], )
    control_rod_cluster_map=models.ForeignKey(ControlRodClusterMap)
    split = models.BooleanField(default=False)
    export = models.BooleanField(default=False)

    class Meta:
        db_table = "egret_follow_case"
        order_with_respect_to = "follow_task"


class CaseAdvancedOption(EgretFollowCase):
    description = models.CharField(max_length=128, blank=True)

    class Meta:
        db_table = "case_advanced_option"


class EgretSequenceTask(AbstractTask):
    follow_task = models.ForeignKey(EgretFollowTask)

    class Meta:
        db_table = "egret_sequence_task"


class EgretSequenceCase(models.Model):
    sequence_task=models.ForeignKey(EgretSequenceTask)
    follow_case = models.ForeignKey(EgretFollowCase, limit_choices_to={"export": True})
    # reactivity coefficient
    FTC = models.BooleanField(default=False)
    MTC = models.BooleanField(default=False)
    DBW = models.BooleanField(default=False)
    ITC = models.BooleanField(default=False)
    # reactivity worth
    MTD = models.BooleanField(default=False)
    FTD = models.BooleanField(default=False)
    ITD = models.BooleanField(default=False)
    PWD = models.BooleanField(default=False)
    XEN = models.BooleanField(default=False)
    SMW = models.BooleanField(default=False)
    # SDM
    SDM = models.BooleanField(default=False)

    class Meta:
        db_table = "egret_sequence_case"
        order_with_respect_to = "sequence_task"


class RodDifferentialWorth(models.Model):
    sequence_case = models.ForeignKey(EgretSequenceCase)
    control_rod_cluster = models.ForeignKey(ControlRodCluster)
    top_step = models.DecimalField(max_digits=10, decimal_places=5, validators=[MinValueValidator(0)])
    bottom_step = models.DecimalField(max_digits=10, decimal_places=5, validators=[MinValueValidator(0)])
    delta_step = models.DecimalField(max_digits=10, decimal_places=5, validators=[MinValueValidator(0)])
    critical_search = models.BooleanField(default=True)

    class Meta:
        db_table = "rod_differential_worth"
        order_with_respect_to = "sequence_case"


class RodIntegralWorth(models.Model):
    sequence_case = models.ForeignKey(EgretSequenceCase)
    start_map = models.ForeignKey(ControlRodClusterMap,related_name="rod_integral_worths")
    end_map = models.ForeignKey(ControlRodClusterMap)
    critical_search = models.BooleanField(default=True)

    class Meta:
        db_table = "rod_integral_worth"
        order_with_respect_to = "sequence_case"



