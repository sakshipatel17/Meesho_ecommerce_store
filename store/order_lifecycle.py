"""
Order Lifecycle Management
Handles order status transitions and business logic
"""

import uuid
from datetime import datetime, timedelta
from django.utils import timezone
from .models import Order


class OrderLifecycle:
    """Manage order lifecycle and status transitions"""
    
    # Status progression timeline
    STATUS_FLOW = {
        'pending': ['processing', 'dispatched', 'shipped', 'out_for_delivery', 'delivered', 'cancelled'],
        'processing': ['dispatched', 'shipped', 'out_for_delivery', 'delivered', 'cancelled'],
        'dispatched': ['shipped', 'out_for_delivery', 'delivered', 'cancelled'],
        'shipped': ['out_for_delivery', 'delivered', 'cancelled'],
        'out_for_delivery': ['delivered', 'cancelled'],
        'delivered': ['return_requested'],  # Can be returned after delivery
        'return_requested': [],  # Final state for returns
        'cancelled': []  # End state
    }
    
    # Timeline events
    TIMELINE_STEPS = [
        ('pending', 'Order Placed'),
        ('processing', 'Processing'),
        ('dispatched', 'Dispatched'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('return_requested', 'Return Requested'),
    ]
    
    # Estimated time for each status (in hours)
    DURATION_IN_HOURS = {
        'pending': 1,  # Takes ~1 hour to process
        'processing': 2,  # Takes ~2 hours to prepare
        'dispatched': 24,  # Takes ~24 hours to dispatch
        'shipped': 24,  # Takes ~24 hours in transit
        'out_for_delivery': 12,  # Takes ~12 hours for delivery
    }
    
    @staticmethod
    def can_transition(current_status, new_status):
        """Check if status transition is allowed"""
        if current_status not in OrderLifecycle.STATUS_FLOW:
            return False
        return new_status in OrderLifecycle.STATUS_FLOW[current_status]
    
    @staticmethod
    def transition_order(order, new_status, admin_action=False):
        """
        Safely transition order to new status
        Returns: (success, message)
        """
        # Normalize status values
        current = order.status.lower() if order.status else 'pending'
        target = new_status.lower()
        
        # Check if transition is allowed
        if not OrderLifecycle.can_transition(current, target):
            return False, f"Cannot transition from {current} to {target}"
        
        # Handle status 'success' → 'processing' auto-transition
        if current == 'success' and target == 'processing':
            order.status = 'processing'
            order.shipped_date = timezone.now()
            return True, "Order moved to processing"
        
        # Update order status and timestamps
        order.status = target
        
        if target == 'dispatched':
            order.shipped_date = timezone.now()
            # Set estimated delivery to 3-5 days from now
            order.estimated_delivery = (timezone.now() + timedelta(days=4)).date()
        
        elif target == 'delivered':
            order.delivered_date = timezone.now()
        
        order.save()
        return True, f"Order status updated to {target}"
    
    @staticmethod
    def get_timeline_progress(order_status):
        """
        Get progress percentage and current step in timeline
        Returns: {current_step, total_steps, percentage, timeline_items}
        """
        status_lower = order_status.lower() if order_status else 'pending'
        
        timeline_items = []
        current_idx = 0
        
        for idx, (status, label) in enumerate(OrderLifecycle.TIMELINE_STEPS):
            is_completed = False
            is_current = False
            
            if status == status_lower:
                is_current = True
                current_idx = idx
            elif status_lower in ['delivered', 'cancelled'] and status_lower == 'delivered':
                is_completed = True
            elif idx < current_idx:
                is_completed = True
            
            timeline_items.append({
                'status': status,
                'label': label,
                'is_completed': is_completed or (status_lower == 'delivered' and status == 'delivered'),
                'is_current': is_current,
            })
        
        # Handle cancelled orders
        if status_lower == 'cancelled':
            timeline_items = [item for item in timeline_items if item['status'] != 'delivered']
            timeline_items.append({
                'status': 'cancelled',
                'label': 'Cancelled',
                'is_completed': True,
                'is_current': False,
            })
        
        percentage = ((current_idx) / (len(OrderLifecycle.TIMELINE_STEPS) - 1)) * 100 if len(OrderLifecycle.TIMELINE_STEPS) > 1 else 0
        
        return {
            'current_step': current_idx,
            'total_steps': len(OrderLifecycle.TIMELINE_STEPS),
            'percentage': min(percentage, 100),
            'timeline_items': timeline_items,
        }
    
    @staticmethod
    def get_estimated_delivery_date(order):
        """Get or calculate estimated delivery date"""
        if order.estimated_delivery:
            return order.estimated_delivery
        
        # If order is not yet dispatched, estimate based on current time
        if order.status in ['pending', 'processing']:
            return (timezone.now() + timedelta(days=5)).date()
        elif order.status == 'dispatched':
            return (timezone.now() + timedelta(days=4)).date()
        elif order.status == 'shipped':
            return (timezone.now() + timedelta(days=3)).date()
        elif order.status == 'out_for_delivery':
            return (timezone.now() + timedelta(days=1)).date()
        else:
            return order.delivered_date.date() if order.delivered_date else None
    
    @staticmethod
    def simulate_auto_progression(order):
        """
        Simulate automatic order progression for demo
        This would be triggered by scheduled tasks in production
        """
        current = order.status.lower()
        
        # Auto-progression sequence for demo
        progression = {
            'success': 'processing',
            'pending': 'processing',
            'processing': 'dispatched',
            'dispatched': 'out_for_delivery',
            'out_for_delivery': 'delivered',
        }
        
        if current in progression:
            next_status = progression[current]
            OrderLifecycle.transition_order(order, next_status)
            return next_status
        
        return current
