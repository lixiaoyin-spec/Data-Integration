<?xml version="1.0" encoding="UTF-8"?>
<!-- 学生信息格式转换: 学院原生格式 → 标准集成格式 -->
<!-- 支持A/B/C三种不同原生格式自动映射 -->
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="xml" encoding="UTF-8" indent="yes"/>

  <xsl:template match="/">
    <Students>
      <xsl:for-each select="Students/student">
        <student>
          <!-- 学号映射: A=Sno, B=sno, C=Sno -->
          <id>
            <xsl:choose>
              <xsl:when test="Sno"><xsl:value-of select="Sno"/></xsl:when>
              <xsl:when test="sno"><xsl:value-of select="sno"/></xsl:when>
              <xsl:when test="Sno"><xsl:value-of select="Sno"/></xsl:when>
              <xsl:otherwise><xsl:value-of select="id"/></xsl:otherwise>
            </xsl:choose>
          </id>
          <!-- 姓名映射: A=Snm, B=sname, C=Snm -->
          <name>
            <xsl:choose>
              <xsl:when test="Snm"><xsl:value-of select="Snm"/></xsl:when>
              <xsl:when test="sname"><xsl:value-of select="sname"/></xsl:when>
              <xsl:when test="Snm"><xsl:value-of select="Snm"/></xsl:when>
              <xsl:otherwise><xsl:value-of select="name"/></xsl:otherwise>
            </xsl:choose>
          </name>
          <!-- 性别映射: A=Sex, B=ssex, C=Sex -->
          <sex>
            <xsl:choose>
              <xsl:when test="Sex"><xsl:value-of select="Sex"/></xsl:when>
              <xsl:when test="ssex"><xsl:value-of select="ssex"/></xsl:when>
              <xsl:when test="Sex"><xsl:value-of select="Sex"/></xsl:when>
              <xsl:otherwise><xsl:value-of select="sex"/></xsl:otherwise>
            </xsl:choose>
          </sex>
          <!-- 专业映射: A=Sde, B=native(无此字段), C=Sde -->
          <major>
            <xsl:choose>
              <xsl:when test="Sde"><xsl:value-of select="Sde"/></xsl:when>
              <xsl:when test="native"><xsl:value-of select="native"/></xsl:when>
              <xsl:when test="Sde"><xsl:value-of select="Sde"/></xsl:when>
              <xsl:otherwise><xsl:value-of select="major"/></xsl:otherwise>
            </xsl:choose>
          </major>
        </student>
      </xsl:for-each>
    </Students>
  </xsl:template>

</xsl:stylesheet>
