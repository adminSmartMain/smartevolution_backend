import boto3
import csv
import io
import uuid
import json
import os
from datetime import datetime
from django.conf import settings
import logging
from functools import wraps

logger = logging.getLogger(__name__)

class S3ExecutionLogger:
    def __init__(self, view_name, user=None, opId=None, s3_bucket=None, s3_path=None):
        self.view_name = view_name
        self.user = user
        self.opId = opId
        self.execution_id = str(uuid.uuid4())
        self.start_time = datetime.now()
        self.steps = []
        
        # Configuración S3
        self.s3_bucket = s3_bucket or getattr(settings, 'AWS_LOGS_BUCKET', 'devsmartevolution')
        self.s3_path = s3_path or 'logs_buyorder'
        
        # Cliente S3
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        
        # Log inicial
        self.log_step('EXECUTION_STARTED', {
            'view': view_name,
            'user': str(user) if user else 'unknown',
            'opId': opId
        })

    def log_step(self, step_name, details=None, debug_message=None):
        """Registra un paso de la ejecución"""
        step_data = {
            'timestamp': datetime.now().isoformat(),
            'execution_id': self.execution_id,
            'view_name': self.view_name,
            'step_name': step_name,
            'user': str(self.user) if self.user else 'unknown',
            'opId': self.opId,
            'details': json.dumps(details, default=str) if details else None,
            'debug_message': debug_message
        }
        
        self.steps.append(step_data)
        
        # Escribir inmediatamente a S3
        self._write_step_to_s3(step_data)
        
        # Mantener logger original si se proporciona mensaje
        if debug_message:
            logger.debug(debug_message)

    def _write_step_to_s3(self, step_data):
        """Escribe un paso individual al CSV en S3"""
        try:
            # Nombre del archivo por día para mejor organización
            date_str = datetime.now().strftime('%Y-%m-%d')
            filename = f"{self.s3_path}/execution_logs_{date_str}.csv"
            
            # Preparar datos para CSV
            csv_data = {
                'execution_id': step_data['execution_id'],
                'timestamp': step_data['timestamp'],
                'view_name': step_data['view_name'],
                'step_name': step_data['step_name'],
                'user': step_data['user'],
                'opId': step_data['opId'] or '',
                'details': step_data['details'] or '',
                'debug_message': step_data['debug_message'] or ''
            }
            
            # Verificar si el archivo existe en S3
            try:
                existing_content = self.s3_client.get_object(
                    Bucket=self.s3_bucket, 
                    Key=filename
                )
                file_exists = True
                existing_body = existing_content['Body'].read().decode('utf-8')
            except self.s3_client.exceptions.NoSuchKey:
                file_exists = False
                existing_body = ""
            
            # Preparar nuevo contenido
            output = io.StringIO()
            fieldnames = ['execution_id', 'timestamp', 'view_name', 'step_name', 'user', 'opId', 'details', 'debug_message']
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            
            if not file_exists:
                writer.writeheader()
            elif existing_body:
                # Agregar el contenido existente
                output.write(existing_body)
            
            writer.writerow(csv_data)
            
            # Subir a S3
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=filename,
                Body=output.getvalue(),
                ContentType='text/csv'
            )
            
        except Exception as e:
            logger.error(f"Error writing to S3: {str(e)}")
            # Fallback: escribir localmente si S3 falla
            self._write_step_local(step_data)

    def _write_step_local(self, step_data):
        """Fallback para escribir localmente si S3 falla"""
        try:
            log_dir = '/tmp/logs'  # Usar /tmp en Lambda o servidor
            os.makedirs(log_dir, exist_ok=True)
            
            date_str = datetime.now().strftime('%Y-%m-%d')
            filepath = f"{log_dir}/execution_logs_{date_str}.csv"
            file_exists = os.path.isfile(filepath)
            
            with open(filepath, 'a', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['execution_id', 'timestamp', 'view_name', 'step_name', 'user', 'opId', 'details', 'debug_message']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                if not file_exists:
                    writer.writeheader()
                
                writer.writerow(step_data)
                
        except Exception as e:
            logger.error(f"Error writing local log: {str(e)}")

    def log_error(self, error_message, exception=None, request_data=None):
        """Registra un error con todos los pasos previos"""
        error_data = {
            'timestamp': datetime.now().isoformat(),
            'execution_id': self.execution_id,
            'view_name': self.view_name,
            'step_name': 'ERROR',
            'user': str(self.user) if self.user else 'unknown',
            'opId': self.opId,
            'details': json.dumps({
                'error_message': error_message,
                'exception': str(exception) if exception else None,
                'request_data': request_data,
                'all_steps_count': len(self.steps),
                'execution_duration_seconds': (datetime.now() - self.start_time).total_seconds()
            }, default=str),
            'debug_message': f"ERROR: {error_message} - Exception: {str(exception)}"
        }
        
        self._write_error_to_s3(error_data)
        logger.error(f"Execution failed: {error_message}")

    def _write_error_to_s3(self, error_data):
        """Escribe información de error al CSV en S3"""
        try:
            date_str = datetime.now().strftime('%Y-%m-%d')
            filename = f"{self.s3_path}/error_logs_{date_str}.csv"
            
            # Verificar si el archivo existe
            try:
                existing_content = self.s3_client.get_object(Bucket=self.s3_bucket, Key=filename)
                file_exists = True
                existing_body = existing_content['Body'].read().decode('utf-8')
            except self.s3_client.exceptions.NoSuchKey:
                file_exists = False
                existing_body = ""
            
            # Preparar nuevo contenido
            output = io.StringIO()
            fieldnames = ['execution_id', 'timestamp', 'view_name', 'step_name', 'user', 'opId', 'details', 'debug_message']
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            
            if not file_exists:
                writer.writeheader()
            elif existing_body:
                output.write(existing_body)
            
            writer.writerow(error_data)
            
            # Subir a S3
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=filename,
                Body=output.getvalue(),
                ContentType='text/csv'
            )
            
        except Exception as e:
            logger.error(f"Error writing error to S3: {str(e)}")

    def complete_execution(self, success=True, additional_data=None):
        """Marca la finalización de la ejecución"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        completion_data = {
            'timestamp': end_time.isoformat(),
            'execution_id': self.execution_id,
            'view_name': self.view_name,
            'step_name': 'EXECUTION_COMPLETED',
            'user': str(self.user) if self.user else 'unknown',
            'opId': self.opId,
            'details': json.dumps({
                'success': success,
                'duration_seconds': duration,
                'total_steps': len(self.steps),
                'additional_data': additional_data
            }, default=str),
            'debug_message': f"Execution completed - Success: {success}, Duration: {duration}s"
        }
        
        self._write_step_to_s3(completion_data)
        
        return {
            'execution_id': self.execution_id,
            'duration_seconds': duration,
            'total_steps': len(self.steps),
            'success': success
        }


def log_execution_to_s3(view_name=None, log_user=True, s3_bucket=None, s3_path=None):
    """
    Decorador para logging automático en vistas
    
    Args:
        view_name (str): Nombre de la vista para logging
        log_user (bool): Si se debe loguear el usuario
        s3_bucket (str): Bucket S3 personalizado
        s3_path (str): Ruta S3 personalizada
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(self, request, *args, **kwargs):
            # Determinar nombre de la vista
            actual_view_name = view_name or self.__class__.__name__
            user = request.user if log_user and hasattr(request, 'user') else None
            
            # Inicializar logger
            execution_logger = S3ExecutionLogger(
                view_name=actual_view_name,
                user=user,
                s3_bucket=s3_bucket,
                s3_path=s3_path
            )
            
            # Adjuntar logger al request para acceso en métodos internos
            request._execution_logger = execution_logger
            
            try:
                # Log de inicio de request
                execution_logger.log_step('REQUEST_START', {
                    'method': request.method,
                    'path': request.path,
                    'content_type': request.content_type
                })
                
                # Ejecutar la vista original
                response = view_func(self, request, *args, **kwargs)
                
                # Log de respuesta
                execution_logger.log_step('REQUEST_COMPLETE', {
                    'status_code': response.status_code,
                    'success': response.status_code < 400
                })
                
                # Completar ejecución
                execution_logger.complete_execution(
                    success=response.status_code < 400,
                    additional_data={'status_code': response.status_code}
                )
                
                return response
                
            except Exception as e:
                # Log de error
                execution_logger.log_error(
                    error_message=str(e),
                    exception=e,
                    request_data=getattr(request, 'data', {})
                )
                execution_logger.complete_execution(success=False)
                raise
        
        return wrapper
    return decorator