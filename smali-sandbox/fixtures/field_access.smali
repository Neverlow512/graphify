.class public Lcom/example/FieldUser;
.super Ljava/lang/Object;

.field private intVal:I
.field private longVal:J
.field private objVal:Ljava/lang/Object;
.field private boolVal:Z
.field private byteVal:B
.field private charVal:C
.field private shortVal:S

.field private static staticInt:I
.field private static staticLong:J
.field private static staticObj:Ljava/lang/Object;
.field private static staticBool:Z
.field private static staticByte:B
.field private static staticChar:C
.field private static staticShort:S

.method public readAllInstance()V
    .registers 3
    iget v0, p0, Lcom/example/FieldUser;->intVal:I
    iget-wide v0, p0, Lcom/example/FieldUser;->longVal:J
    iget-object v0, p0, Lcom/example/FieldUser;->objVal:Ljava/lang/Object;
    iget-boolean v0, p0, Lcom/example/FieldUser;->boolVal:Z
    iget-byte v0, p0, Lcom/example/FieldUser;->byteVal:B
    iget-char v0, p0, Lcom/example/FieldUser;->charVal:C
    iget-short v0, p0, Lcom/example/FieldUser;->shortVal:S
    return-void
.end method

.method public writeAllInstance()V
    .registers 3
    const/4 v0, 0x0
    iput v0, p0, Lcom/example/FieldUser;->intVal:I
    iput-wide v0, p0, Lcom/example/FieldUser;->longVal:J
    iput-object v0, p0, Lcom/example/FieldUser;->objVal:Ljava/lang/Object;
    iput-boolean v0, p0, Lcom/example/FieldUser;->boolVal:Z
    iput-byte v0, p0, Lcom/example/FieldUser;->byteVal:B
    iput-char v0, p0, Lcom/example/FieldUser;->charVal:C
    iput-short v0, p0, Lcom/example/FieldUser;->shortVal:S
    return-void
.end method

.method public static readAllStatic()V
    .registers 2
    sget v0, Lcom/example/FieldUser;->staticInt:I
    sget-wide v0, Lcom/example/FieldUser;->staticLong:J
    sget-object v0, Lcom/example/FieldUser;->staticObj:Ljava/lang/Object;
    sget-boolean v0, Lcom/example/FieldUser;->staticBool:Z
    sget-byte v0, Lcom/example/FieldUser;->staticByte:B
    sget-char v0, Lcom/example/FieldUser;->staticChar:C
    sget-short v0, Lcom/example/FieldUser;->staticShort:S
    return-void
.end method

.method public static writeAllStatic()V
    .registers 2
    const/4 v0, 0x0
    sput v0, Lcom/example/FieldUser;->staticInt:I
    sput-wide v0, Lcom/example/FieldUser;->staticLong:J
    sput-object v0, Lcom/example/FieldUser;->staticObj:Ljava/lang/Object;
    sput-boolean v0, Lcom/example/FieldUser;->staticBool:Z
    sput-byte v0, Lcom/example/FieldUser;->staticByte:B
    sput-char v0, Lcom/example/FieldUser;->staticChar:C
    sput-short v0, Lcom/example/FieldUser;->staticShort:S
    return-void
.end method
