from exceptions import NotImplementedError, TypeError

from django.db import models
from djangotoolbox.fields import ListField


class RelatedManagerFactory(object):
    managers = {}

    @staticmethod
    def get(superclass):
        manager = RelatedManagerFactory.managers.get(superclass, None)
        if manager:
            return manager
        else:
            class RelatedManager(superclass):
                def __init__(self, instance, field):
                    super(RelatedManager, self).__init__()
                    self.rel_instance = instance
                    self.rel_field = field
                    self.model = field.othermodel
                    self.superclass = superclass

                def get_query_set(self):
                    # TODO: this may need changes for multi-db

                    helper_field_name = self.rel_field.helper_field_name
                    filter_values = {"pk__in":getattr(self.rel_instance, helper_field_name)}
                    return super(RelatedManager, self).get_query_set().filter(**filter_values)
                
                def add(self, *objs):
                    cur_vals = self._get_pk_list()
                    obj_pks  = self._get_pk_list(objs)
                    new_vals = [obj for obj in obj_pks if obj not in cur_vals]
                    new_vals = new_vals + cur_vals

                    self._local_save(new_vals)
                    
                def remove(self, *objs):
                    cur_vals = self._get_pk_list()
                    obj_pks  = self._get_pk_list(objs)
                    new_vals = [val for val in cur_vals if val not in obj_pks]

                    self._local_save(new_vals)

                def clear(self):
                    self._local_save([])

                def create(self, **kwargs):
                    Model = self.rel_field.othermodel
                    new_obj = Model(**kwargs)
                    new_obj.save()
                    cur_vals = self._get_pk_list()
                    cur_vals.append(new_obj.pk)

                    self._local_save(cur_vals)

                def _local_save(self, new_vals):
                    setattr(self.rel_instance, self.rel_field.helper_field_name, new_vals)

                    # HACK: some methods are expected to automatically save
                    Model = self.rel_instance.__class__
                    tempobj = Model._base_manager.filter(pk=self.rel_instance.pk)[0]

                    setattr(tempobj, self.rel_field.helper_field_name, new_vals)
                    tempobj.save() 

                def _get_pk_list(self, value=None):
                    if value is None:
                        return getattr(self.rel_instance, self.rel_field.helper_field_name)

                    # This will do a database lookup to determine if the related objs exist.
                    # Not in use because it is determined to be inefficient.
                    # value = self.get_query_set() if value is None else value

                    try:
                        if isinstance(value, (models.query.QuerySet, models.Manager)) and \
                                      hasattr(value, 'all'):
                            values = []
                            for subval in value.all():
                                if not isinstance(subval, self.rel_field.othermodel):
                                    raise TypeError("Unknown type for member of list "
                                                    "or tuple: %s" % subval.__class__)
                                values.append(subval.pk)
                        elif isinstance(value, (list, tuple)):
                            values = []
                            for subval in value:
                                if not isinstance(subval, self.rel_field.othermodel):
                                    raise TypeError("Unknown type for member of list "
                                                    "or tuple: %s" % subval.__class__)
                                values.append(subval.pk)
                        else:
                            raise TypeError("Unknown type in conversion: %s" % value.__class__)
                                                 
                    except TypeError, e:
                        raise e
                    except Exception, e:
                        raise TypeError("Unknown Error in conversion: %s, %s" % 
                                        (e.__class__, e.message))
                    return values

            return RelatedManager


class ManyToManyField(object):
    
    def __init__(self, othermodel, **kwargs):
        is_symetrical = False
        lazy_eval = False

        if isinstance(othermodel, basestring):
            if othermodel == "self":
               is_symetrical = True
            else:
               lazy_evel = True

        elif issubclass(othermodel, models.Model):
            self.othermodel = othermodel

        if is_symetrical or lazy_eval:
            raise NotImplementedError

        base_manager_class = self.othermodel._base_manager.__class__
        self.RelatedManager = RelatedManagerFactory.get(base_manager_class)

        super(ManyToManyField, self).__init__(**kwargs)

    def contribute_to_class(self, cls, name):
        self.name = name
        self.model = cls
        cls._meta.add_virtual_field(self)

        self.helper_field_name = "__" + self.name + "_helper"
        setattr(cls, self.name, self)

        field = ListField(models.ForeignKey(self.othermodel))
        setattr(cls, self.helper_field_name, field)
        getattr(cls, self.helper_field_name).contribute_to_class(cls, self.helper_field_name)

    def value_from_object(self, obj):
        "Returns the value of this field in the given model instance."
        getattr(obj, self.name).all()

    def __get__(self, instance, instance_type=None):
        if instance is None:
            return self

        values = getattr(instance, self.helper_field_name)
        manager = self.RelatedManager(instance, self)
        return manager

    def __set__(self, instance, value):
        if not isinstance(value, (tuple, list)):
            value = list(value)
        manager = self.RelatedManager(instance, self)
        setattr(instance, self.helper_field_name, value)



class Product(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField()

    def __str__(self):
        return "<Product name=%s, description=%s>" % (self.name, self.description)


class Company(models.Model):
    name = models.CharField(max_length=40)
    tagline = models.CharField(max_length=60)
    products = ManyToManyField(Product)

    def __str__(self):
        prod = unicode([str(prod) for prod in self.products.all()])
        return "<Company name=%s, tagline=%s, products=%s>" % (self.name, self.tagline, prod)


def test():
    """
    >>> test()
    """
    Product(name="plane", description="Human flight.").save()
    Product(name="car", description="A method of ground transportation.").save()
    Product(name="eggs", description="Tomorrow's breakfast.").save()
    Product(name="cart", description="Something to push groceries in.").save()

    Company(name="foodmart", tagline="A place for groceries.").save()
    Company(name="Buy-It-All", tagline="Anything you can imagine.").save()
    Company(name="Go-Co", tagline="All your transportation needs.").save()

    import testlib; testlib.pdb_trace()
    cos = Company.objects.all()
    prs = Product.objects.all()
    c1 = cos[0]
    p1 = prs[0]

    c1.products.add(p1)

    "pause"
